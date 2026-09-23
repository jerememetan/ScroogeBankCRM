# Churn Lambda Inference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Lambda-compatible churn scorer that converts the approved CRM client, account, and transaction request into the exact Version 2 model feature row.

**Architecture:** `AI/get_churn_probability.py` remains independently deployable and owns validation, calendar-ledger aggregation, lazy artifact loading, prediction, and the two invocation modes. Pure feature construction returns a dictionary so unit tests do not need the model; prediction alone converts that dictionary into a metadata-ordered pandas DataFrame.

**Tech Stack:** Python 3.11, standard library, pandas, joblib, scikit-learn, XGBoost, pytest

---

## File structure

- Create: `AI/tests/test_get_churn_probability.py` — contract, feature, invocation, and model smoke tests.
- Modify: `AI/get_churn_probability.py` — validation, ledger aggregation, prediction, and Lambda handler.
- Create: `AI/requirements.txt` — local and Lambda-container Python dependencies shared by both scorers.

### Task 1: Lock the churn feature contract with failing tests

**Files:**
- Create: `AI/tests/test_get_churn_probability.py`
- Test: `AI/tests/test_get_churn_probability.py`

- [ ] **Step 1: Add a representative request fixture and exact feature assertions**

```python
from copy import deepcopy
from datetime import date
from unittest.mock import patch

import pytest

from AI import get_churn_probability as churn


@pytest.fixture
def request_body():
    return {
        "asOfDate": "2026-09-23",
        "client": {
            "clientId": "C1002",
            "gender": "Female",
            "city": "Singapore",
            "dateOfBirth": "1990-07-22",
        },
        "account": {
            "accountId": "A5678",
            "clientId": "C1002",
            "accountType": "Checking",
            "accountStatus": "Active",
            "openingDate": "2022-09-01",
            "initialDeposit": 5000.0,
            "currency": "SGD",
            "branchId": "SG-001",
        },
        "transactions": [
            {
                "id": "T1000", "accountId": "A5678", "clientId": "C1002",
                "transaction": "DEPOSIT", "direction": "INCOMING", "amount": 1000.0,
                "date": "2026-08-15", "status": "COMPLETED", "balanceAfter": 6000.0,
                "counterpartyReference": None,
            },
            {
                "id": "T1001", "accountId": "A5678", "clientId": "C1002",
                "transaction": "DEPOSIT", "direction": "INCOMING", "amount": 2400.0,
                "date": "2026-09-05", "status": "COMPLETED", "balanceAfter": 8400.0,
                "counterpartyReference": None,
            },
            {
                "id": "T1002", "accountId": "A5678", "clientId": "C1002",
                "transaction": "PAYMENT", "direction": "OUTGOING", "amount": 800.0,
                "date": "2026-09-10", "status": "COMPLETED", "balanceAfter": 7600.0,
                "counterpartyReference": "MERCHANT-042",
            },
            {
                "id": "T1003", "accountId": "A5678", "clientId": "C1002",
                "transaction": "TRANSFER", "direction": "OUTGOING", "amount": 999.0,
                "date": "2026-09-20", "status": "FAILED", "balanceAfter": None,
                "counterpartyReference": "ACCOUNT-991",
            },
        ],
    }


def test_build_features_uses_only_completed_transactions(request_body):
    features = churn.build_features(request_body)

    assert features["client_age_years"] == 36
    assert features["client_tenure_months"] == 48
    assert features["account_current_balance"] == 7600.0
    assert features["account_previous_month_end_balance"] == 6000.0
    assert features["transaction_current_month_credit_total"] == 2400.0
    assert features["transaction_current_month_debit_total"] == 800.0
    assert features["transaction_previous_month_credit_total"] == 1000.0
    assert features["transaction_previous_month_debit_total"] == 0.0
    assert features["transaction_days_since_last_activity"] == 13
    assert features["account_balance_change_month"] == 1600.0
    assert features["transaction_current_net_flow"] == 1600.0
    assert features["transaction_previous_net_flow"] == 1000.0
    assert features["transaction_credit_change"] == 1400.0
    assert features["transaction_debit_change"] == 800.0
    assert features["transaction_debit_to_balance"] == pytest.approx(800.0 / 7601.0)
    assert features["transaction_credit_to_balance"] == pytest.approx(2400.0 / 7601.0)


def test_daily_balances_are_calendar_day_averages(request_body):
    features = churn.build_features(request_body)
    expected_current = ((4 * 6000.0) + (5 * 8400.0) + (14 * 7600.0)) / 23
    expected_previous = ((14 * 5000.0) + (17 * 6000.0)) / 31

    assert features["account_current_month_average_balance"] == pytest.approx(expected_current)
    assert features["account_previous_month_average_balance"] == pytest.approx(expected_previous)
    assert features["account_average_balance_change_month"] == pytest.approx(
        expected_current - expected_previous
    )
```

- [ ] **Step 2: Add validation tests for the agreed CRM schema**

```python
@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda body: body["account"].update(currency="USD"), "currency"),
        (lambda body: body["transactions"][0].pop("direction"), "direction"),
        (lambda body: body["transactions"][0].update(accountId="OTHER"), "accountId"),
        (lambda body: body["transactions"][0].update(clientId="OTHER"), "clientId"),
        (lambda body: body["transactions"][0].update(date="2020-01-01"), "openingDate"),
        (lambda body: body["transactions"][0].update(amount=float("inf")), "amount"),
    ],
)
def test_invalid_contract_is_rejected(request_body, mutation, message):
    invalid = deepcopy(request_body)
    mutation(invalid)
    with pytest.raises(ValueError, match=message):
        churn.build_features(invalid)
```

- [ ] **Step 3: Run the churn feature tests and confirm the expected import failure**

Run: `python -m pytest AI/tests/test_get_churn_probability.py -q`

Expected: FAIL because the empty module has no `build_features` function.

### Task 2: Implement churn validation and calendar-ledger features

**Files:**
- Modify: `AI/get_churn_probability.py`
- Test: `AI/tests/test_get_churn_probability.py`

- [ ] **Step 1: Add constants, strict parsers, and calendar helpers**

Implement these exact interfaces:

```python
VALID_TYPES = {"DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "DEBIT"}
VALID_DIRECTIONS = {"INCOMING", "OUTGOING"}
VALID_STATUSES = {"COMPLETED", "PENDING", "FAILED"}

def _required(mapping, key, path): ...
def _parse_date(value, path): ...
def _nonempty_string(value, path): ...
def _nonnegative_number(value, path): ...
def _completed_months(start, end): ...
def _month_start(value): ...
def _quarter_start(value): ...
```

`_parse_date` uses `date.fromisoformat`, verifies round-trip `YYYY-MM-DD`, and raises `ValueError(f"{path} must use YYYY-MM-DD")`. `_nonnegative_number` rejects booleans, non-numbers, non-finite values, and negatives. `_completed_months` subtracts one when the end day precedes the start day.

- [ ] **Step 2: Add transaction normalization and ledger helpers**

```python
def _signed_amount(transaction):
    return transaction["amount"] if transaction["direction"] == "INCOMING" else -transaction["amount"]


def _balance_through(initial_deposit, transactions, end_date):
    return initial_deposit + sum(
        _signed_amount(item)
        for item in transactions
        if item["status"] == "COMPLETED" and item["date"] <= end_date
    )


def _average_daily_balance(initial_deposit, transactions, opening_date, start_date, end_date):
    effective_start = max(opening_date, start_date)
    if effective_start > end_date:
        return 0.0
    balance = _balance_through(initial_deposit, transactions, effective_start - timedelta(days=1))
    by_date = defaultdict(float)
    for item in transactions:
        if item["status"] == "COMPLETED" and effective_start <= item["date"] <= end_date:
            by_date[item["date"]] += _signed_amount(item)
    total = 0.0
    current = effective_start
    while current <= end_date:
        balance += by_date[current]
        total += balance
        current += timedelta(days=1)
    return total / ((end_date - effective_start).days + 1)
```

Validate every transaction's IDs against the enclosing client/account. Enforce `DEPOSIT` as incoming, `WITHDRAWAL`, `PAYMENT`, and `DEBIT` as outgoing, and allow `TRANSFER` in either direction. Validate all statuses, but include only `COMPLETED` items dated on or before `asOfDate` in ledger calculations.

- [ ] **Step 3: Implement `build_features(payload)`**

Construct all 25 metadata fields. Use the account opening date as last activity when no completed transaction exists, treat the initial deposit as opening-day starting balance but not monthly transaction credit, and calculate ratios with `abs(current_balance) + 1.0`. Determine quarter windows from the quarter containing `asOfDate`: previous completed quarter, then the quarter immediately before it.

Before returning, assert the keys equal this set:

```python
EXPECTED_FEATURES = {
    "client_gender", "client_city", "account_branch_id", "client_tenure_months",
    "client_age_years", "account_current_balance", "account_previous_month_end_balance",
    "account_avg_balance_previous_quarter", "account_avg_balance_previous_two_quarters",
    "transaction_current_month_credit_total", "transaction_previous_month_credit_total",
    "transaction_current_month_debit_total", "transaction_previous_month_debit_total",
    "account_current_month_average_balance", "account_previous_month_average_balance",
    "transaction_days_since_last_activity", "account_balance_change_month",
    "account_average_balance_change_month", "account_average_balance_change_quarter",
    "transaction_current_net_flow", "transaction_previous_net_flow",
    "transaction_credit_change", "transaction_debit_change",
    "transaction_debit_to_balance", "transaction_credit_to_balance",
}
```

- [ ] **Step 4: Run the churn feature tests**

Run: `python -m pytest AI/tests/test_get_churn_probability.py -q`

Expected: PASS for feature and validation tests.

- [ ] **Step 5: Commit the feature builder**

```bash
git add AI/get_churn_probability.py AI/tests/test_get_churn_probability.py
git commit -m "feat: derive churn model features from CRM data"
```

### Task 3: Add churn prediction and both Lambda invocation modes

**Files:**
- Modify: `AI/tests/test_get_churn_probability.py`
- Modify: `AI/get_churn_probability.py`

- [ ] **Step 1: Add fake-pipeline tests for ordering, thresholding, and responses**

```python
class FakePipeline:
    def __init__(self, probability):
        self.probability = probability
        self.columns = None

    def predict_proba(self, frame):
        self.columns = list(frame.columns)
        return [[1.0 - self.probability, self.probability]]


def test_predict_orders_features_from_metadata(request_body):
    features = churn.build_features(request_body)
    metadata = {
        "model_name": "test-churn", "model_version": "2.0.0",
        "output_field": "churn_probability", "suggested_review_threshold": 0.34,
        "advisory_use_only": True, "feature_columns": list(reversed(features)),
    }
    pipeline = FakePipeline(0.34)
    with patch.object(churn, "_load_artifacts", return_value=(pipeline, metadata)):
        result = churn.predict_churn(request_body)

    assert pipeline.columns == metadata["feature_columns"]
    assert result["classification"] == "CHURN"
    assert result["is_positive"] is True
    assert result["probability"] == 0.34
    assert result["accountId"] == "A5678"
    assert result["clientId"] == "C1002"


def test_api_gateway_and_direct_invocation(request_body):
    expected = {"classification": "NOT_CHURN"}
    with patch.object(churn, "predict_churn", return_value=expected):
        assert churn.lambda_handler(request_body, None) == expected
        response = churn.lambda_handler({"body": json.dumps(request_body)}, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == expected


def test_api_gateway_validation_error_returns_400():
    response = churn.lambda_handler({"body": "{"}, None)
    assert response["statusCode"] == 400
    assert "error" in json.loads(response["body"])
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run: `python -m pytest AI/tests/test_get_churn_probability.py -q`

Expected: FAIL because prediction, artifact loading, and `lambda_handler` are not defined.

- [ ] **Step 3: Implement lazy artifacts and `predict_churn`**

Use module-relative paths from `Path(__file__).resolve().parent / "models"`. Cache pipeline and metadata in module-level variables. Reorder the one-row pandas DataFrame with `metadata["feature_columns"]`, reject missing or extra feature keys, call `predict_proba`, compare the unrounded probability with the metadata threshold, then return model details, identifiers, classification, `is_positive`, six-decimal probability, threshold, and `advisory_only`.

- [ ] **Step 4: Implement `lambda_handler(event, context)`**

Treat a dictionary containing `body` as API Gateway. Parse a string JSON object, return `400` for malformed JSON or `ValueError`, and return a generic `500` body `{"error": "Inference failed"}` for other exceptions. Direct invocation calls `predict_churn` and allows unexpected exceptions to propagate.

- [ ] **Step 5: Run all churn unit tests**

Run: `python -m pytest AI/tests/test_get_churn_probability.py -q`

Expected: PASS.

- [ ] **Step 6: Commit the completed churn handler**

```bash
git add AI/get_churn_probability.py AI/tests/test_get_churn_probability.py
git commit -m "feat: expose churn scoring Lambda handler"
```

### Task 4: Verify the real churn artifact and deployment dependencies

**Files:**
- Create: `AI/requirements.txt`
- Modify: `AI/tests/test_get_churn_probability.py`

- [ ] **Step 1: Add the runtime/test dependency list**

```text
joblib
pandas
scikit-learn
xgboost
pytest
```

- [ ] **Step 2: Add a real-model smoke test guarded by dependency availability**

```python
def test_real_churn_pipeline_smoke(request_body):
    pytest.importorskip("xgboost")
    churn._PIPELINE = None
    churn._METADATA = None
    result = churn.predict_churn(request_body)
    assert 0.0 <= result["probability"] <= 1.0
    assert result["model"] == "crm_churn_xgboost"
    assert result["model_version"] == "2.0.0"
```

- [ ] **Step 3: Run the complete churn test file**

Run: `python -m pytest AI/tests/test_get_churn_probability.py -q`

Expected: all unit tests PASS; the real-model test either PASSes or is explicitly SKIPPED only when XGBoost is unavailable.

- [ ] **Step 4: Commit the dependency and smoke-test change**

```bash
git add AI/requirements.txt AI/tests/test_get_churn_probability.py
git commit -m "test: smoke test downloaded churn model"
```
