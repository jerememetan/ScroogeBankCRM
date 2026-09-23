# Scam Lambda Inference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Lambda-compatible scam scorer that converts the approved outgoing CRM transaction request into the exact Version 2 model feature row.

**Architecture:** `AI/get_scam_probability.py` remains independently deployable and owns request validation, transaction-type normalization, date/history features, lazy artifact loading, prediction, and the two invocation modes. Pure feature construction returns a dictionary; prediction converts it to a metadata-ordered one-row DataFrame.

**Tech Stack:** Python 3.11, standard library, pandas, joblib, scikit-learn, XGBoost, pytest

---

## File structure

- Create: `AI/tests/test_get_scam_probability.py` — contract, feature, invocation, and model smoke tests.
- Modify: `AI/get_scam_probability.py` — validation, scam feature construction, prediction, and Lambda handler.
- Reuse: `AI/requirements.txt` — dependencies created by the churn plan.

### Task 1: Lock the scam feature contract with failing tests

**Files:**
- Create: `AI/tests/test_get_scam_probability.py`
- Test: `AI/tests/test_get_scam_probability.py`

- [ ] **Step 1: Add a representative request and exact feature assertions**

```python
from copy import deepcopy
from unittest.mock import patch
import json
import math

import pytest

from AI import get_scam_probability as scam


@pytest.fixture
def request_body():
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


def test_build_features_matches_model_contract(request_body):
    features = scam.build_features(request_body)

    assert features["transaction_type"] == "TRANSFER"
    assert features["transaction_amount"] == 1200.0
    assert features["transaction_day_index"] == 22
    assert features["transaction_hour_of_day"] == 0
    assert features["transaction_log_amount"] == pytest.approx(math.log1p(1200.0))
    assert features["transaction_week_index"] == 3
    assert features["transaction_day_of_week"] == 1
    assert features["hour_sin"] == 0.0
    assert features["hour_cos"] == 1.0
    assert features["amount_if_transfer"] == 1200.0
    assert features["amount_if_cash_out"] == 0.0
    assert features["amount_if_payment"] == 0.0
    assert features["amount_if_cash_in"] == 0.0
    assert features["amount_if_debit"] == 0.0
    assert features["destination_prior_count"] == 2
    assert features["destination_prior_count_log"] == pytest.approx(math.log1p(2))
    assert features["destination_age_steps"] == 72
    assert features["destination_is_merchant"] == 0
```

- [ ] **Step 2: Add normalization and validation tests**

```python
def test_withdrawal_normalizes_to_cash_out(request_body):
    body = deepcopy(request_body)
    body["transaction"].update(transaction="WITHDRAWAL", amount=50.0)
    features = scam.build_features(body)
    assert features["transaction_type"] == "CASH_OUT"
    assert features["amount_if_cash_out"] == 50.0


def test_payment_is_marked_as_merchant(request_body):
    body = deepcopy(request_body)
    body["transaction"].update(transaction="PAYMENT")
    assert scam.build_features(body)["destination_is_merchant"] == 1


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda body: body["transaction"].update(direction="INCOMING"), "OUTGOING"),
        (lambda body: body["transaction"].pop("direction"), "direction"),
        (lambda body: body["transaction"].update(transaction="CRYPTO"), "transaction"),
        (lambda body: body["transaction"].update(amount=-1), "amount"),
        (lambda body: body.update(historyStartDate="2026-10-01"), "historyStartDate"),
        (lambda body: body.update(counterpartyHistoryDates="2026-09-20"), "list"),
        (lambda body: body["transaction"].update(counterpartyReference=""), "counterpartyReference"),
    ],
)
def test_invalid_contract_is_rejected(request_body, mutation, message):
    invalid = deepcopy(request_body)
    mutation(invalid)
    with pytest.raises(ValueError, match=message):
        scam.build_features(invalid)
```

- [ ] **Step 3: Run the scam feature tests and confirm the expected import failure**

Run: `python -m pytest AI/tests/test_get_scam_probability.py -q`

Expected: FAIL because the empty module has no `build_features` function.

### Task 2: Implement scam validation and feature construction

**Files:**
- Modify: `AI/get_scam_probability.py`
- Test: `AI/tests/test_get_scam_probability.py`

- [ ] **Step 1: Add constants and strict parsers**

```python
TYPE_MAPPING = {
    "DEPOSIT": "CASH_IN",
    "WITHDRAWAL": "CASH_OUT",
    "TRANSFER": "TRANSFER",
    "PAYMENT": "PAYMENT",
    "DEBIT": "DEBIT",
}
VALID_STATUSES = {"COMPLETED", "PENDING", "FAILED"}
EXPECTED_FEATURES = {
    "transaction_type", "transaction_amount", "transaction_day_index",
    "transaction_hour_of_day", "transaction_log_amount", "transaction_week_index",
    "transaction_day_of_week", "hour_sin", "hour_cos", "amount_if_transfer",
    "amount_if_cash_out", "amount_if_payment", "amount_if_cash_in", "amount_if_debit",
    "destination_prior_count", "destination_prior_count_log", "destination_age_steps",
    "destination_is_merchant",
}
```

Implement `_required`, `_parse_date`, `_nonempty_string`, and `_nonnegative_number` with the same strict rules as the churn module. Validate the transaction ID, account ID, client ID, type, direction, amount, date, and status. Require a non-empty `counterpartyReference` for `TRANSFER` and `PAYMENT`.

- [ ] **Step 2: Implement `build_features(payload)`**

Require `direction == "OUTGOING"`. Calculate `day_index = (transaction_date - history_start_date).days` and reject negative values. Parse every history date; count only dates strictly earlier than the transaction date. Use the earliest prior date for `destination_age_steps`, with one calendar day equal to 24 steps. Map application types through `TYPE_MAPPING`, create the five mutually exclusive amount columns, and set merchant to one only for `PAYMENT`.

Return exactly the 18 keys in `EXPECTED_FEATURES`, using `math.log1p` for amount and prior count. Same-day and future history dates remain valid input but do not count as prior history.

- [ ] **Step 3: Run the scam feature tests**

Run: `python -m pytest AI/tests/test_get_scam_probability.py -q`

Expected: PASS for feature, normalization, and validation tests.

- [ ] **Step 4: Commit the scam feature builder**

```bash
git add AI/get_scam_probability.py AI/tests/test_get_scam_probability.py
git commit -m "feat: derive scam model features from CRM data"
```

### Task 3: Add scam prediction and both Lambda invocation modes

**Files:**
- Modify: `AI/tests/test_get_scam_probability.py`
- Modify: `AI/get_scam_probability.py`

- [ ] **Step 1: Add fake-pipeline tests for ordering, thresholding, and responses**

```python
class FakePipeline:
    def __init__(self, probability):
        self.probability = probability
        self.columns = None

    def predict_proba(self, frame):
        self.columns = list(frame.columns)
        return [[1.0 - self.probability, self.probability]]


def test_predict_orders_features_and_uses_metadata_threshold(request_body):
    features = scam.build_features(request_body)
    metadata = {
        "model_name": "test-scam", "model_version": "2.0.0",
        "output_field": "scam_probability", "suggested_review_threshold": 0.20,
        "advisory_use_only": True, "feature_columns": list(reversed(features)),
    }
    pipeline = FakePipeline(0.20)
    with patch.object(scam, "_load_artifacts", return_value=(pipeline, metadata)):
        result = scam.predict_scam(request_body)

    assert pipeline.columns == metadata["feature_columns"]
    assert result["classification"] == "SCAM"
    assert result["is_positive"] is True
    assert result["probability"] == 0.20
    assert result["transactionId"] == "T2001"


def test_api_gateway_and_direct_invocation(request_body):
    expected = {"classification": "NOT_SCAM"}
    with patch.object(scam, "predict_scam", return_value=expected):
        assert scam.lambda_handler(request_body, None) == expected
        response = scam.lambda_handler({"body": json.dumps(request_body)}, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == expected


def test_api_gateway_inference_error_returns_generic_500(request_body):
    with patch.object(scam, "predict_scam", side_effect=RuntimeError("secret path")):
        response = scam.lambda_handler({"body": json.dumps(request_body)}, None)
    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"error": "Inference failed"}
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run: `python -m pytest AI/tests/test_get_scam_probability.py -q`

Expected: FAIL because prediction, artifact loading, and `lambda_handler` are not defined.

- [ ] **Step 3: Implement lazy artifacts and `predict_scam`**

Load and cache `models/crm_scam_pipeline.joblib` and `models/crm_scam_metadata.json` relative to `__file__`. Check generated feature keys against `metadata["feature_columns"]`, build a one-row DataFrame in that order, call `predict_proba`, compare the unrounded probability to the metadata threshold, and return model details, transaction/account/client identifiers, classification, `is_positive`, six-decimal probability, threshold, and `advisory_only`.

- [ ] **Step 4: Implement `lambda_handler(event, context)`**

Use the same invocation distinction and status behavior as churn: direct objects return directly and validation raises; API Gateway string bodies return `200`, validation/malformed JSON return `400`, and unexpected failures return generic `500` without stack traces or local paths.

- [ ] **Step 5: Run all scam unit tests**

Run: `python -m pytest AI/tests/test_get_scam_probability.py -q`

Expected: PASS.

- [ ] **Step 6: Commit the completed scam handler**

```bash
git add AI/get_scam_probability.py AI/tests/test_get_scam_probability.py
git commit -m "feat: expose scam scoring Lambda handler"
```

### Task 4: Verify the real scam artifact and combined suite

**Files:**
- Modify: `AI/tests/test_get_scam_probability.py`
- Verify: `AI/requirements.txt`

- [ ] **Step 1: Add a real-model smoke test guarded by dependency availability**

```python
def test_real_scam_pipeline_smoke(request_body):
    pytest.importorskip("xgboost")
    scam._PIPELINE = None
    scam._METADATA = None
    result = scam.predict_scam(request_body)
    assert 0.0 <= result["probability"] <= 1.0
    assert result["model"] == "crm_scam_risk_xgboost"
    assert result["model_version"] == "2.0.0"
```

- [ ] **Step 2: Run the complete AI test suite**

Run: `python -m pytest AI/tests -q`

Expected: all unit tests PASS; each real-model smoke test either PASSes or is explicitly SKIPPED only when XGBoost is unavailable.

- [ ] **Step 3: Check source syntax independently of model dependencies**

Run: `python -m py_compile AI/get_churn_probability.py AI/get_scam_probability.py`

Expected: exit code 0 with no output.

- [ ] **Step 4: Commit the final scam smoke test**

```bash
git add AI/tests/test_get_scam_probability.py
git commit -m "test: smoke test downloaded scam model"
```
