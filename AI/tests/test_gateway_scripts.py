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
