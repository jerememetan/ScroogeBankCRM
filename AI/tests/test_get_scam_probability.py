"""Contract tests for the scam inference Lambda."""

import json
import math

import pytest

from AI import get_scam_probability as scam


@pytest.fixture
def payload():
    return {
        "historyStartDate": "2026-09-01",
        "transaction": {
            "id": "T2001", "accountId": "A5678", "clientId": "C1002",
            "transaction": "TRANSFER", "direction": "OUTGOING", "amount": 1200.0,
            "date": "2026-09-23", "status": "PENDING", "balanceAfter": None,
            "counterpartyReference": "ACCOUNT-991",
        },
        "counterpartyHistoryDates": ["2026-09-20", "2026-09-21", "2026-09-23", "2026-09-24"],
    }


def test_exact_features_and_prior_history(payload):
    payload["unrecognized"] = "tolerated"
    payload["transaction"]["unrecognized"] = "tolerated"
    features = scam.build_features(payload)
    assert features == {
        "transaction_type": "TRANSFER", "transaction_amount": 1200.0,
        "transaction_day_index": 22, "transaction_hour_of_day": 0,
        "transaction_log_amount": pytest.approx(math.log1p(1200)),
        "transaction_week_index": 3, "transaction_day_of_week": 1,
        "hour_sin": 0.0, "hour_cos": 1.0,
        "amount_if_transfer": 1200.0, "amount_if_cash_out": 0,
        "amount_if_payment": 0, "amount_if_cash_in": 0, "amount_if_debit": 0,
        "destination_prior_count": 2,
        "destination_prior_count_log": pytest.approx(math.log1p(2)),
        "destination_age_steps": 72, "destination_is_merchant": 0,
    }
    assert len(features) == 18


@pytest.mark.parametrize("transaction_type,model_type,amount_column,merchant", [
    ("TRANSFER", "TRANSFER", "amount_if_transfer", 0),
    ("WITHDRAWAL", "CASH_OUT", "amount_if_cash_out", 0),
    ("PAYMENT", "PAYMENT", "amount_if_payment", 1),
    ("DEPOSIT", "CASH_IN", "amount_if_cash_in", 0),
    ("DEBIT", "DEBIT", "amount_if_debit", 0),
])
def test_type_normalization_and_amount_columns(payload, transaction_type, model_type, amount_column, merchant):
    payload["transaction"]["transaction"] = transaction_type
    if transaction_type == "DEPOSIT":
        payload["transaction"]["counterpartyReference"] = None
    features = scam.build_features(payload)
    assert features["transaction_type"] == model_type
    assert features["destination_is_merchant"] == merchant
    for column in ("amount_if_transfer", "amount_if_cash_out", "amount_if_payment",
                   "amount_if_cash_in", "amount_if_debit"):
        assert features[column] == (1200 if column == amount_column else 0)


@pytest.mark.parametrize("status", ["COMPLETED", "PENDING", "FAILED"])
def test_all_documented_statuses_are_accepted(payload, status):
    payload["transaction"]["status"] = status
    assert scam.build_features(payload)["transaction_amount"] == 1200


@pytest.mark.parametrize("path,value", [
    (("historyStartDate",), "2026-09-24"),
    (("historyStartDate",), "2026-9-01"),
    (("transaction", "id"), " "),
    (("transaction", "accountId"), None),
    (("transaction", "clientId"), ""),
    (("transaction", "transaction"), "CASH_OUT"),
    (("transaction", "direction"), "INCOMING"),
    (("transaction", "status"), "OTHER"),
    (("transaction", "amount"), -1),
    (("transaction", "amount"), True),
    (("transaction", "amount"), float("nan")),
    (("transaction", "amount"), float("inf")),
    (("transaction", "amount"), 10 ** 400),
    (("transaction", "date"), "2026-02-30"),
    (("transaction", "date"), "2026-09-23T00:00:00"),
    (("transaction", "balanceAfter"), True),
    (("transaction", "balanceAfter"), float("inf")),
    (("transaction", "balanceAfter"), 10 ** 400),
    (("transaction", "counterpartyReference"), ""),
    (("counterpartyHistoryDates",), "2026-09-20"),
    (("counterpartyHistoryDates",), ["2026-09-20", "2026-9-21"]),
    (("counterpartyHistoryDates",), ["2026-02-30"]),
])
def test_invalid_request_values_raise_request_validation_error(payload, path, value):
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(scam.RequestValidationError):
        scam.build_features(payload)


@pytest.mark.parametrize("path", [
    ("historyStartDate",), ("transaction",), ("counterpartyHistoryDates",),
    ("transaction", "id"), ("transaction", "accountId"),
    ("transaction", "clientId"), ("transaction", "transaction"),
    ("transaction", "direction"), ("transaction", "amount"),
    ("transaction", "date"), ("transaction", "status"),
    ("transaction", "balanceAfter"), ("transaction", "counterpartyReference"),
])
def test_required_keys_rejected_when_missing(payload, path):
    target = payload
    for part in path[:-1]:
        target = target[part]
    del target[path[-1]]
    with pytest.raises(scam.RequestValidationError):
        scam.build_features(payload)


@pytest.mark.parametrize("transaction_type", ["TRANSFER", "PAYMENT"])
def test_counterparty_reference_is_required_for_destination_types(payload, transaction_type):
    payload["transaction"]["transaction"] = transaction_type
    payload["transaction"]["counterpartyReference"] = None
    with pytest.raises(scam.RequestValidationError, match="counterpartyReference"):
        scam.build_features(payload)


@pytest.mark.parametrize("transaction_type", ["WITHDRAWAL", "DEPOSIT", "DEBIT"])
def test_counterparty_reference_can_be_null_for_other_types(payload, transaction_type):
    payload["transaction"]["transaction"] = transaction_type
    payload["transaction"]["counterpartyReference"] = None
    assert len(scam.build_features(payload)) == 18


def test_balance_after_is_informational(payload):
    payload["transaction"]["balanceAfter"] = -999.5
    assert scam.build_features(payload)["transaction_amount"] == 1200


def test_empty_history_has_zero_prior_features(payload):
    payload["counterpartyHistoryDates"] = []
    features = scam.build_features(payload)
    assert features["destination_prior_count"] == 0
    assert features["destination_prior_count_log"] == 0
    assert features["destination_age_steps"] == 0


def test_nonfinite_derived_features_are_request_errors(payload, monkeypatch):
    original_log1p = scam.math.log1p
    monkeypatch.setattr(scam.math, "log1p", lambda value: math.inf if value == 1200 else original_log1p(value))
    with pytest.raises(scam.RequestValidationError, match="finite"):
        scam.build_features(payload)


class FakePipeline:
    def __init__(self, probability=0.2, error=None):
        self.probability = probability
        self.error = error
        self.frame = None

    def predict_proba(self, frame):
        self.frame = frame
        if self.error:
            raise self.error
        return [[1 - self.probability, self.probability]]


def fake_metadata(payload):
    return {
        "feature_columns": list(reversed(scam.build_features(payload))),
        "model_name": "test-model", "model_version": "9",
        "suggested_review_threshold": 0.2, "advisory_use_only": True,
    }


def test_metadata_order_and_unrounded_threshold(payload, monkeypatch):
    info = fake_metadata(payload)
    pipeline = FakePipeline(0.1999999)
    monkeypatch.setattr(scam, "_load_artifacts", lambda: (pipeline, info))
    result = scam.predict_scam(payload)
    assert list(pipeline.frame.columns) == info["feature_columns"]
    assert len(pipeline.frame) == 1
    assert result == {
        "model": "test-model", "model_version": "9",
        "classification": "NOT_SCAM", "is_positive": False,
        "probability": 0.2, "threshold": 0.2, "advisory_only": True,
        "transactionId": "T2001", "accountId": "A5678", "clientId": "C1002",
    }
    pipeline.probability = 0.2
    assert scam.predict_scam(payload)["classification"] == "SCAM"


def test_metadata_key_mismatch_rejected(payload, monkeypatch):
    info = fake_metadata(payload)
    info["feature_columns"][-1] = "unexpected"
    monkeypatch.setattr(scam, "_load_artifacts", lambda: (FakePipeline(), info))
    with pytest.raises(RuntimeError, match="feature"):
        scam.predict_scam(payload)


def test_direct_and_gateway_success(payload, monkeypatch):
    monkeypatch.setattr(scam, "_load_artifacts", lambda: (FakePipeline(), fake_metadata(payload)))
    assert scam.lambda_handler(payload, None)["classification"] == "SCAM"
    response = scam.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"])["transactionId"] == "T2001"


@pytest.mark.parametrize("body", ["{", "[]", "null", "42", None, json.dumps({})])
def test_gateway_bad_body_returns_400(payload, body):
    response = scam.lambda_handler({"body": body}, None)
    assert response["statusCode"] == 400
    assert isinstance(json.loads(response["body"])["error"], str)


def test_gateway_json_integer_over_conversion_limit_returns_400(payload):
    body = json.dumps(payload)
    body = body.replace('"amount": 1200.0', '"amount": ' + '9' * 5000)
    response = scam.lambda_handler({"body": body}, None)
    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "body must contain valid JSON"}


def test_direct_validation_error_propagates(payload):
    payload["transaction"]["direction"] = "INCOMING"
    with pytest.raises(scam.RequestValidationError):
        scam.lambda_handler(payload, None)


@pytest.mark.parametrize("error", [RuntimeError("C:/private/model.joblib"),
                                   ValueError("C:/private/model.joblib")])
def test_gateway_internal_errors_are_generic_and_direct_errors_propagate(payload, monkeypatch, error):
    monkeypatch.setattr(scam, "_load_artifacts",
                        lambda: (FakePipeline(error=error), fake_metadata(payload)))
    response = scam.lambda_handler({"body": json.dumps(payload)}, None)
    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"error": "Inference failed"}
    assert "private" not in response["body"]
    with pytest.raises(type(error), match="private"):
        scam.lambda_handler(payload, None)


def test_real_model_smoke(payload):
    pytest.importorskip("xgboost")
    result = scam.predict_scam(payload)
    assert 0 <= result["probability"] <= 1
    assert result["model"] == "crm_scam_risk_xgboost"
