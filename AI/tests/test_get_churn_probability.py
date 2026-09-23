import json
from datetime import date

import pytest

from AI import get_churn_probability as churn


@pytest.fixture
def payload():
    def tx(id, kind, direction, amount, when, status="COMPLETED"):
        return {"id": id, "accountId": "A1", "clientId": "C1", "transaction": kind,
                "direction": direction, "amount": amount, "date": when, "status": status}
    return {
        "asOfDate": "2026-09-23",
        "client": {"clientId": "C1", "gender": "Female", "city": "Singapore", "dateOfBirth": "1990-09-24"},
        "account": {"accountId": "A1", "clientId": "C1", "accountType": "Checking",
                    "accountStatus": "Active", "openingDate": "2026-08-01",
                    "initialDeposit": 5000.0, "currency": "SGD", "branchId": "SG-001"},
        "transactions": [tx("T1", "DEPOSIT", "INCOMING", 1000, "2026-08-15"),
                         tx("T2", "TRANSFER", "INCOMING", 2400, "2026-09-05"),
                         tx("T3", "PAYMENT", "OUTGOING", 800, "2026-09-10"),
                         tx("T4", "DEBIT", "OUTGOING", 999, "2026-09-20", "FAILED")],
    }


def test_feature_values_and_exact_set(payload):
    f = churn.build_features(payload)
    with open(churn.MODELS_DIR / "crm_churn_metadata.json", encoding="utf-8") as stream:
        assert set(f) == set(json.load(stream)["feature_columns"])
    assert len(f) == 25
    assert (f["client_gender"], f["client_city"], f["account_branch_id"]) == ("Female", "Singapore", "SG-001")
    assert (f["client_age_years"], f["client_tenure_months"]) == (35, 1)
    expected = {
        "account_current_balance": 7600, "account_previous_month_end_balance": 6000,
        "transaction_current_month_credit_total": 2400, "transaction_previous_month_credit_total": 1000,
        "transaction_current_month_debit_total": 800, "transaction_previous_month_debit_total": 0,
        "transaction_days_since_last_activity": 13, "account_balance_change_month": 1600,
        "account_avg_balance_previous_quarter": 0, "account_avg_balance_previous_two_quarters": 0,
        "account_average_balance_change_quarter": 0, "transaction_current_net_flow": 1600,
        "transaction_previous_net_flow": 1000, "transaction_credit_change": 1400,
        "transaction_debit_change": 800,
    }
    for key, value in expected.items():
        assert f[key] == value
    current_avg = (4 * 6000 + 5 * 8400 + 14 * 7600) / 23
    previous_avg = (14 * 5000 + 17 * 6000) / 31
    assert f["account_current_month_average_balance"] == pytest.approx(current_avg)
    assert f["account_previous_month_average_balance"] == pytest.approx(previous_avg)
    assert f["account_average_balance_change_month"] == pytest.approx(current_avg - previous_avg)
    assert f["transaction_debit_to_balance"] == pytest.approx(800 / 7601)
    assert f["transaction_credit_to_balance"] == pytest.approx(2400 / 7601)


def test_quarter_closing_balance_and_opening_fallback(payload):
    payload["asOfDate"] = "2027-01-03"
    payload["account"]["openingDate"] = "2026-04-01"
    payload["transactions"][0]["date"] = "2026-04-01"
    payload["transactions"][1]["date"] = "2026-10-02"
    payload["transactions"][2]["date"] = "2026-10-02"
    payload["transactions"].pop()
    f = churn.build_features(payload)
    assert f["account_avg_balance_previous_quarter"] == pytest.approx((6000 + 91 * 7600) / 92)
    assert f["account_avg_balance_previous_two_quarters"] == 6000
    assert f["account_average_balance_change_quarter"] == pytest.approx((6000 + 91 * 7600) / 92 - 6000)
    payload["transactions"] = []
    assert churn.build_features(payload)["transaction_days_since_last_activity"] == (date(2027, 1, 3) - date(2026, 4, 1)).days


@pytest.mark.parametrize("path,value", [
    (("client", "clientId"), ""), (("client", "dateOfBirth"), "1990-02-30"),
    (("account", "openingDate"), "2026-09-24"), (("account", "currency"), "USD"),
    (("account", "clientId"), "C2"), (("account", "initialDeposit"), float("nan")),
    (("transactions", 0, "accountId"), "A2"), (("transactions", 0, "clientId"), "C2"),
    (("transactions", 0, "direction"), "OUTGOING"), (("transactions", 0, "amount"), -1),
    (("transactions", 0, "date"), "2026-07-31"), (("transactions", 0, "date"), "2026-09-24"),
    (("transactions", 3, "direction"), None), (("transactions", 1, "status"), "OTHER"),
])
def test_invalid_input_rejected(payload, path, value):
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        churn.build_features(payload)


@pytest.mark.parametrize("path", [
    ("asOfDate",), ("client", "gender"), ("client", "city"),
    ("account", "accountType"), ("account", "accountStatus"), ("account", "branchId"),
    ("transactions", 0, "id"), ("transactions", 0, "status"), ("transactions", 0, "direction"),
])
def test_missing_fields_rejected(payload, path):
    target = payload
    for part in path[:-1]:
        target = target[part]
    del target[path[-1]]
    with pytest.raises(ValueError):
        churn.build_features(payload)


class FakePipeline:
    def __init__(self, probability=0.34, error=None):
        self.probability, self.error, self.frame = probability, error, None

    def predict_proba(self, frame):
        if self.error:
            raise self.error
        self.frame = frame
        return [[1 - self.probability, self.probability]]


def fake_metadata(payload):
    return {"feature_columns": list(reversed(churn.build_features(payload))),
            "model_name": "test-model", "model_version": "9",
            "suggested_review_threshold": 0.34, "advisory_use_only": True}


def test_prediction_order_and_unrounded_threshold(payload, monkeypatch):
    info, pipeline = fake_metadata(payload), FakePipeline(0.3399999)
    monkeypatch.setattr(churn, "_load_artifacts", lambda: (pipeline, info))
    result = churn.predict_churn(payload)
    assert list(pipeline.frame.columns) == info["feature_columns"]
    assert result == {"model": "test-model", "model_version": "9",
                      "classification": "NOT_CHURN", "is_positive": False,
                      "probability": 0.34, "threshold": 0.34,
                      "advisory_only": True, "clientId": "C1", "accountId": "A1"}
    pipeline.probability = 0.34
    assert churn.predict_churn(payload)["classification"] == "CHURN"


def test_direct_and_gateway_invocation(payload, monkeypatch):
    monkeypatch.setattr(churn, "_load_artifacts", lambda: (FakePipeline(), fake_metadata(payload)))
    assert churn.lambda_handler(payload, None)["classification"] == "CHURN"
    response = churn.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"])["clientId"] == "C1"
    for body in ("{", json.dumps({}), None):
        response = churn.lambda_handler({"body": body}, None)
        assert response["statusCode"] == 400
        assert "error" in json.loads(response["body"])
    with pytest.raises(ValueError):
        churn.lambda_handler({}, None)


def test_gateway_inference_failure_is_generic(payload, monkeypatch):
    monkeypatch.setattr(churn, "_load_artifacts",
                        lambda: (FakePipeline(error=RuntimeError("private path")), fake_metadata(payload)))
    response = churn.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"error": "Inference failed"}
    with pytest.raises(RuntimeError, match="private path"):
        churn.lambda_handler(payload, None)


def test_real_model_smoke(payload):
    pytest.importorskip("xgboost")
    result = churn.predict_churn(payload)
    assert 0 <= result["probability"] <= 1
    assert result["model"] == "crm_churn_xgboost"
