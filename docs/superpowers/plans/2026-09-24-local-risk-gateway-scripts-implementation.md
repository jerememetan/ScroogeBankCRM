# Local Risk Gateway Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide separately named local scripts that print real scam and churn model predictions.

**Architecture:** Keep both Lambda handlers unchanged. Each small script owns one fictional request payload and invokes its corresponding handler directly; a subprocess test verifies both scripts load the real artifacts and print the expected model identity.

**Tech Stack:** Python 3.11, pytest, existing joblib model pipelines

---

### Task 1: Add and verify the two local scripts

**Files:**
- Rename: `AI/gateway.py` to `AI/scam_gateway.py`
- Create: `AI/churn_gateway.py`
- Create: `AI/tests/test_gateway_scripts.py`

- [ ] **Step 1: Write the failing subprocess test**

```python
import ast
import subprocess
import sys
from pathlib import Path

import pytest


AI_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("script_name", "model_name"),
    [
        ("scam_gateway.py", "crm_scam_risk_xgboost"),
        ("churn_gateway.py", "crm_churn_xgboost"),
    ],
)
def test_gateway_script_prints_real_prediction(script_name, model_name):
    completed = subprocess.run(
        [sys.executable, str(AI_DIR / script_name)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = ast.literal_eval(completed.stdout.strip())
    assert result["model"] == model_name
    assert 0.0 <= result["probability"] <= 1.0
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m pytest AI/tests/test_gateway_scripts.py -q`

Expected: FAIL because `scam_gateway.py` and `churn_gateway.py` do not exist.

- [ ] **Step 3: Rename the scam script and create the churn script**

Keep the existing scam script content unchanged under `AI/scam_gateway.py`. Create `AI/churn_gateway.py` with this structure:

```python
from get_churn_probability import lambda_handler

event = {
    "asOfDate": "2026-09-24",
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
            "id": "T1001", "accountId": "A5678", "clientId": "C1002",
            "transaction": "DEPOSIT", "direction": "INCOMING", "amount": 2400.0,
            "date": "2026-09-05", "status": "COMPLETED", "balanceAfter": 7400.0,
            "counterpartyReference": None,
        },
        {
            "id": "T1002", "accountId": "A5678", "clientId": "C1002",
            "transaction": "PAYMENT", "direction": "OUTGOING", "amount": 800.0,
            "date": "2026-09-10", "status": "COMPLETED", "balanceAfter": 6600.0,
            "counterpartyReference": "MERCHANT-042",
        },
    ],
}

result = lambda_handler(event, None)
print(result)
```

- [ ] **Step 4: Run both script tests and the full AI suite**

Run: `python -m pytest AI/tests/test_gateway_scripts.py -q`

Expected: 2 passed.

Run: `python -m pytest AI/tests -q`

Expected: all tests pass.

- [ ] **Step 5: Run both scripts directly**

Run: `python AI/scam_gateway.py`

Expected: a `crm_scam_risk_xgboost` response.

Run: `python AI/churn_gateway.py`

Expected: a `crm_churn_xgboost` response.
