"""Churn inference from a validated CRM account snapshot."""

import json
import math
from datetime import date, timedelta
from pathlib import Path

import joblib
import pandas as pd


MODELS_DIR = Path(__file__).resolve().parent / "models"
_ARTIFACTS = None


class RequestValidationError(ValueError):
    """The scoring request does not satisfy the input contract."""


def _object(value, name):
    if not isinstance(value, dict):
        raise RequestValidationError(f"{name} must be an object")
    return value


def _string(obj, key, name):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError(f"{name}.{key} must be a nonempty string")
    return value


def _date(obj, key, name):
    value = _string(obj, key, name)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise RequestValidationError(f"{name}.{key} must be a valid YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise RequestValidationError(f"{name}.{key} must be a valid YYYY-MM-DD date")
    return parsed


def _amount(obj, key, name):
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RequestValidationError(f"{name}.{key} must be a finite nonnegative number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise RequestValidationError(f"{name}.{key} must be a finite nonnegative number") from exc
    if not math.isfinite(number) or number < 0:
        raise RequestValidationError(f"{name}.{key} must be a finite nonnegative number")
    return number


def _balance_after(item, name):
    if "balanceAfter" not in item:
        raise RequestValidationError(f"{name}.balanceAfter is required")
    value = item["balanceAfter"]
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RequestValidationError(f"{name}.balanceAfter must be null or a finite number")
    try:
        finite = math.isfinite(float(value))
    except OverflowError as exc:
        raise RequestValidationError(f"{name}.balanceAfter must be null or a finite number") from exc
    if not finite:
        raise RequestValidationError(f"{name}.balanceAfter must be null or a finite number")


def _month_start(day):
    return day.replace(day=1)


def _previous_month_start(day):
    month_start = day.replace(day=1)
    if month_start == date.min:
        return None
    return (month_start - timedelta(days=1)).replace(day=1)


def _quarter_start(day):
    return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)


def _completed_months(start, end):
    months = (end.year - start.year) * 12 + end.month - start.month
    return months - (end.day < start.day)


def build_features(payload):
    """Return the 25 model fields for a single account snapshot."""
    payload = _object(payload, "payload")
    as_of = _date(payload, "asOfDate", "payload")
    client = _object(payload.get("client"), "client")
    account = _object(payload.get("account"), "account")
    client_id = _string(client, "clientId", "client")
    gender = _string(client, "gender", "client")
    city = _string(client, "city", "client")
    birth = _date(client, "dateOfBirth", "client")
    account_id = _string(account, "accountId", "account")
    account_client_id = _string(account, "clientId", "account")
    _string(account, "accountType", "account")
    _string(account, "accountStatus", "account")
    opening = _date(account, "openingDate", "account")
    initial = _amount(account, "initialDeposit", "account")
    currency = _string(account, "currency", "account")
    branch = _string(account, "branchId", "account")
    if birth > as_of or opening > as_of:
        raise RequestValidationError("dateOfBirth and openingDate must be on or before asOfDate")
    if account_client_id != client_id:
        raise RequestValidationError("account.clientId does not match client.clientId")
    if currency != "SGD":
        raise RequestValidationError("account.currency must be SGD")

    transactions = payload.get("transactions")
    if not isinstance(transactions, list):
        raise RequestValidationError("transactions must be an array")
    completed = []
    for index, item in enumerate(transactions):
        name = f"transactions[{index}]"
        item = _object(item, name)
        _string(item, "id", name)
        tx_account = _string(item, "accountId", name)
        tx_client = _string(item, "clientId", name)
        kind = _string(item, "transaction", name)
        direction = _string(item, "direction", name)
        amount = _amount(item, "amount", name)
        when = _date(item, "date", name)
        status = _string(item, "status", name)
        _balance_after(item, name)
        if tx_account != account_id or tx_client != client_id:
            raise RequestValidationError(f"{name} identifiers do not match account and client")
        if when < opening or when > as_of:
            raise RequestValidationError(f"{name}.date is outside the scoring snapshot")
        if kind not in {"DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "DEBIT"}:
            raise RequestValidationError(f"{name}.transaction is invalid")
        if direction not in {"INCOMING", "OUTGOING"}:
            raise RequestValidationError(f"{name}.direction is invalid")
        if (kind == "DEPOSIT" and direction != "INCOMING") or (
            kind in {"WITHDRAWAL", "PAYMENT", "DEBIT"} and direction != "OUTGOING"
        ):
            raise RequestValidationError(f"{name}.direction conflicts with transaction")
        if status not in {"COMPLETED", "PENDING", "FAILED"}:
            raise RequestValidationError(f"{name}.status is invalid")
        if status == "COMPLETED":
            completed.append((when, amount if direction == "INCOMING" else -amount))

    current_start = _month_start(as_of)
    previous_start = _previous_month_start(as_of)
    previous_end = current_start - timedelta(days=1) if previous_start is not None else None
    quarter_start = _quarter_start(as_of)
    previous_quarter_end = quarter_start - timedelta(days=1) if quarter_start > date.min else None
    previous_quarter_start = _quarter_start(previous_quarter_end) if previous_quarter_end else None
    two_quarters_end = (
        previous_quarter_start - timedelta(days=1)
        if previous_quarter_start is not None and previous_quarter_start > date.min else None
    )
    two_quarters_start = _quarter_start(two_quarters_end) if two_quarters_end else None

    def balance_at(day):
        if day is None or day < opening:
            return 0
        return initial + sum(signed for when, signed in completed if when <= day)

    def mean_daily_closing(start, end):
        if start is None or end is None:
            return 0
        start = max(start, opening)
        if start > end:
            return 0
        days = (end - start).days + 1
        return sum(balance_at(start + timedelta(days=i)) for i in range(days)) / days

    def monthly_flows(start, end):
        if start is None or end is None:
            return 0, 0
        credits = sum(signed for when, signed in completed if start <= when <= end and signed > 0)
        debits = -sum(signed for when, signed in completed if start <= when <= end and signed < 0)
        return credits, debits

    current_balance = balance_at(as_of)
    previous_balance = balance_at(previous_end)
    current_credit, current_debit = monthly_flows(current_start, as_of)
    previous_credit, previous_debit = monthly_flows(previous_start, previous_end)
    current_average = mean_daily_closing(current_start, as_of)
    previous_average = mean_daily_closing(previous_start, previous_end)
    previous_quarter_average = mean_daily_closing(previous_quarter_start, previous_quarter_end)
    two_quarters_average = mean_daily_closing(two_quarters_start, two_quarters_end)
    last_activity = max((when for when, _ in completed), default=opening)
    denominator = abs(current_balance) + 1.0

    return {
        "client_gender": gender,
        "client_city": city,
        "account_branch_id": branch,
        "client_tenure_months": _completed_months(opening, as_of),
        "client_age_years": _completed_months(birth, as_of) // 12,
        "account_current_balance": current_balance,
        "account_previous_month_end_balance": previous_balance,
        "account_avg_balance_previous_quarter": previous_quarter_average,
        "account_avg_balance_previous_two_quarters": two_quarters_average,
        "transaction_current_month_credit_total": current_credit,
        "transaction_previous_month_credit_total": previous_credit,
        "transaction_current_month_debit_total": current_debit,
        "transaction_previous_month_debit_total": previous_debit,
        "account_current_month_average_balance": current_average,
        "account_previous_month_average_balance": previous_average,
        "transaction_days_since_last_activity": (as_of - last_activity).days,
        "account_balance_change_month": current_balance - previous_balance,
        "account_average_balance_change_month": current_average - previous_average,
        "account_average_balance_change_quarter": previous_quarter_average - two_quarters_average,
        "transaction_current_net_flow": current_credit - current_debit,
        "transaction_previous_net_flow": previous_credit - previous_debit,
        "transaction_credit_change": current_credit - previous_credit,
        "transaction_debit_change": current_debit - previous_debit,
        "transaction_debit_to_balance": current_debit / denominator,
        "transaction_credit_to_balance": current_credit / denominator,
    }


def _load_artifacts():
    global _ARTIFACTS
    if _ARTIFACTS is None:
        with (MODELS_DIR / "crm_churn_metadata.json").open(encoding="utf-8") as stream:
            metadata = json.load(stream)
        pipeline = joblib.load(MODELS_DIR / "crm_churn_pipeline.joblib")
        _ARTIFACTS = (pipeline, metadata)
    return _ARTIFACTS


def predict_churn(payload):
    features = build_features(payload)
    pipeline, metadata = _load_artifacts()
    columns = metadata["feature_columns"]
    if len(columns) != len(features) or set(columns) != set(features):
        raise RuntimeError("Model metadata feature columns do not match generated features")
    frame = pd.DataFrame([[features[column] for column in columns]], columns=columns)
    probability = float(pipeline.predict_proba(frame)[0][1])
    threshold = metadata["suggested_review_threshold"]
    positive = probability >= threshold
    return {
        "model": metadata["model_name"],
        "model_version": metadata["model_version"],
        "classification": "CHURN" if positive else "NOT_CHURN",
        "is_positive": positive,
        "probability": round(probability, 6),
        "threshold": threshold,
        "advisory_only": metadata["advisory_use_only"],
        "clientId": payload["client"]["clientId"],
        "accountId": payload["account"]["accountId"],
    }


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


def lambda_handler(event, context):
    if not isinstance(event, dict) or "body" not in event:
        return predict_churn(event)
    try:
        if not isinstance(event["body"], str):
            raise RequestValidationError("body must be a JSON string object")
        try:
            payload = json.loads(event["body"])
        except json.JSONDecodeError as exc:
            raise RequestValidationError("body must contain valid JSON") from exc
        if not isinstance(payload, dict):
            raise RequestValidationError("body must contain a JSON object")
        return _response(200, predict_churn(payload))
    except RequestValidationError as exc:
        return _response(400, {"error": str(exc)})
    except Exception:
        return _response(500, {"error": "Inference failed"})
