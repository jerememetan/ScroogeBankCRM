import json
from datetime import date

import pytest

from AI import get_churn_probability as churn


@pytest.fixture
def payload():
    def tx(id, kind, direction, amount, when, status="COMPLETED"):
        return {"id": id, "accountId": "A1", "clientId": "C1", "transaction": kind,
                "direction": direction, "amount": amount, "date": when, "status": status,
                "balanceAfter": None}
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


@pytest.mark.parametrize("field,old", [
    ("initialDeposit", "5000.0"),
    ("amount", "1000"),
])
def test_gateway_json_integer_over_conversion_limit_returns_400(payload, field, old):
    body = json.dumps(payload)
    original = f'"{field}": {old}'
    assert original in body
    body = body.replace(original, f'"{field}": ' + '9' * 5000, 1)
    response = churn.lambda_handler({"body": body}, None)
    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "body must contain valid JSON"}


def test_gateway_inference_failure_is_generic(payload, monkeypatch):
    monkeypatch.setattr(churn, "_load_artifacts",
                        lambda: (FakePipeline(error=RuntimeError("private path")), fake_metadata(payload)))
    response = churn.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"error": "Inference failed"}
    with pytest.raises(RuntimeError, match="private path"):
        churn.lambda_handler(payload, None)


def test_gateway_pipeline_value_error_is_generic(payload, monkeypatch):
    private_path = "C:/private/model.joblib"
    monkeypatch.setattr(churn, "_load_artifacts",
                        lambda: (FakePipeline(error=ValueError(private_path)), fake_metadata(payload)))
    response = churn.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"error": "Inference failed"}
    assert private_path not in response["body"]
    with pytest.raises(ValueError, match="private/model"):
        churn.lambda_handler(payload, None)


def test_balance_after_is_required_even_when_transaction_failed(payload):
    del payload["transactions"][-1]["balanceAfter"]
    with pytest.raises(ValueError, match="balanceAfter"):
        churn.build_features(payload)


@pytest.mark.parametrize("value", [True, "7600", float("nan"), float("inf"), -float("inf")])
def test_balance_after_rejects_nonfinite_or_nonnumeric_values(payload, value):
    payload["transactions"][0]["balanceAfter"] = value
    with pytest.raises(ValueError, match="balanceAfter"):
        churn.build_features(payload)


def test_balance_after_is_informational(payload):
    payload["transactions"][0]["balanceAfter"] = -999.5
    assert churn.build_features(payload)["account_current_balance"] == 7600


@pytest.mark.parametrize("path", [("account", "initialDeposit"), ("transactions", 0, "amount")])
def test_enormous_integer_is_request_validation_error(payload, path):
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = 10 ** 400
    with pytest.raises(ValueError, match="finite nonnegative"):
        churn.build_features(payload)


def test_finite_inputs_cannot_produce_nonfinite_derived_features(payload):
    payload["account"]["initialDeposit"] = 1e308
    payload["transactions"][1]["amount"] = 1e308
    with pytest.raises(churn.RequestValidationError, match="finite"):
        churn.build_features(payload)


def test_negative_derived_balance_remains_valid(payload):
    payload["account"]["initialDeposit"] = 0
    payload["transactions"] = [payload["transactions"][2]]
    f = churn.build_features(payload)
    assert f["account_current_balance"] == -800
    assert f["transaction_debit_to_balance"] == pytest.approx(800 / 801)


@pytest.mark.parametrize("as_of", ["0001-01-01", "0001-04-01"])
def test_year_one_history_windows_are_empty_and_finite(payload, as_of):
    payload["asOfDate"] = as_of
    payload["client"]["dateOfBirth"] = "0001-01-01"
    payload["account"]["openingDate"] = "0001-01-01"
    payload["transactions"] = []
    f = churn.build_features(payload)
    assert f["account_current_balance"] == 5000
    expected_previous = 0 if as_of == "0001-01-01" else 5000
    assert f["account_previous_month_end_balance"] == expected_previous
    assert f["account_avg_balance_previous_two_quarters"] == 0
    assert f["transaction_days_since_last_activity"] == (date.fromisoformat(as_of) - date.min).days
    assert all(not isinstance(value, (int, float)) or float("-inf") < value < float("inf")
               for value in f.values())


def test_real_model_smoke(payload):
    pytest.importorskip("xgboost")
    result = churn.predict_churn(payload)
    assert 0 <= result["probability"] <= 1
    assert result["model"] == "crm_churn_xgboost"
