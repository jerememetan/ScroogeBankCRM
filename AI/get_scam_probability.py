"""Scam inference from a validated outgoing CRM transaction."""

import json
import math
from datetime import date
from pathlib import Path

import joblib
import pandas as pd


MODELS_DIR = Path(__file__).resolve().parent / "models"
_ARTIFACTS = None
_TRANSACTION_TYPES = {
    "DEPOSIT": "CASH_IN", "WITHDRAWAL": "CASH_OUT", "TRANSFER": "TRANSFER",
    "PAYMENT": "PAYMENT", "DEBIT": "DEBIT",
}
_AMOUNT_COLUMNS = {
    "TRANSFER": "amount_if_transfer", "CASH_OUT": "amount_if_cash_out",
    "PAYMENT": "amount_if_payment", "CASH_IN": "amount_if_cash_in",
    "DEBIT": "amount_if_debit",
}


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


def _date_value(value, name):
    if not isinstance(value, str):
        raise RequestValidationError(f"{name} must be a valid YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise RequestValidationError(f"{name} must be a valid YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise RequestValidationError(f"{name} must be a valid YYYY-MM-DD date")
    return parsed


def _finite_number(value, name, nonnegative=False):
    message = f"{name} must be a finite {'nonnegative ' if nonnegative else ''}number"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RequestValidationError(message)
    try:
        number = float(value)
    except OverflowError as exc:
        raise RequestValidationError(message) from exc
    if not math.isfinite(number) or (nonnegative and number < 0):
        raise RequestValidationError(message)
    return number


def build_features(payload):
    """Validate a request and return exactly the 18 scam model features."""
    payload = _object(payload, "payload")
    start = _date_value(payload.get("historyStartDate"), "historyStartDate")
    transaction = _object(payload.get("transaction"), "transaction")
    for key in ("id", "accountId", "clientId"):
        _string(transaction, key, "transaction")
    kind = _string(transaction, "transaction", "transaction")
    if kind not in _TRANSACTION_TYPES:
        raise RequestValidationError("transaction.transaction is invalid")
    direction = _string(transaction, "direction", "transaction")
    if direction != "OUTGOING":
        raise RequestValidationError("transaction.direction must be OUTGOING")
    amount = _finite_number(transaction.get("amount"), "transaction.amount", nonnegative=True)
    when = _date_value(transaction.get("date"), "transaction.date")
    if start > when:
        raise RequestValidationError("historyStartDate must be on or before transaction.date")
    status = _string(transaction, "status", "transaction")
    if status not in {"COMPLETED", "PENDING", "FAILED"}:
        raise RequestValidationError("transaction.status is invalid")
    if "balanceAfter" not in transaction:
        raise RequestValidationError("transaction.balanceAfter is required")
    if transaction["balanceAfter"] is not None:
        _finite_number(transaction["balanceAfter"], "transaction.balanceAfter")
    if "counterpartyReference" not in transaction:
        raise RequestValidationError("transaction.counterpartyReference is required")
    counterparty = transaction["counterpartyReference"]
    if kind in {"TRANSFER", "PAYMENT"}:
        if not isinstance(counterparty, str) or not counterparty.strip():
            raise RequestValidationError("transaction.counterpartyReference must be a nonempty string")
    elif counterparty is not None and not isinstance(counterparty, str):
        raise RequestValidationError("transaction.counterpartyReference must be null or a string")

    history = payload.get("counterpartyHistoryDates")
    if not isinstance(history, list):
        raise RequestValidationError("counterpartyHistoryDates must be an array")
    prior = []
    for index, value in enumerate(history):
        history_date = _date_value(value, f"counterpartyHistoryDates[{index}]")
        if history_date < when:
            prior.append(history_date)

    model_type = _TRANSACTION_TYPES[kind]
    day_index = (when - start).days
    features = {
        "transaction_type": model_type,
        "transaction_amount": amount,
        "transaction_day_index": day_index,
        "transaction_hour_of_day": 0,
        "transaction_log_amount": math.log1p(amount),
        "transaction_week_index": day_index // 7,
        "transaction_day_of_week": day_index % 7,
        "hour_sin": 0.0,
        "hour_cos": 1.0,
    }
    features.update({column: amount if model_type == label else 0
                     for label, column in _AMOUNT_COLUMNS.items()})
    features.update({
        "destination_prior_count": len(prior),
        "destination_prior_count_log": math.log1p(len(prior)),
        "destination_age_steps": (when - min(prior)).days * 24 if prior else 0,
        "destination_is_merchant": int(kind == "PAYMENT"),
    })
    for name, value in features.items():
        if isinstance(value, (int, float)) and not math.isfinite(value):
            raise RequestValidationError(f"derived feature {name} must be finite")
    return features


def _load_artifacts():
    global _ARTIFACTS
    if _ARTIFACTS is None:
        with (MODELS_DIR / "crm_scam_metadata.json").open(encoding="utf-8") as stream:
            metadata = json.load(stream)
        pipeline = joblib.load(MODELS_DIR / "crm_scam_pipeline.joblib")
        _ARTIFACTS = (pipeline, metadata)
    return _ARTIFACTS


def predict_scam(payload):
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
        "classification": "SCAM" if positive else "NOT_SCAM",
        "is_positive": positive,
        "probability": round(probability, 6),
        "threshold": threshold,
        "advisory_only": metadata["advisory_use_only"],
        "transactionId": payload["transaction"]["id"],
        "accountId": payload["transaction"]["accountId"],
        "clientId": payload["transaction"]["clientId"],
    }


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


def lambda_handler(event, context):
    if not isinstance(event, dict) or "body" not in event:
        return predict_scam(event)
    try:
        if not isinstance(event["body"], str):
            raise RequestValidationError("body must be a JSON string object")
        try:
            payload = json.loads(event["body"])
        except ValueError as exc:
            raise RequestValidationError("body must contain valid JSON") from exc
        if not isinstance(payload, dict):
            raise RequestValidationError("body must contain a JSON object")
        return _response(200, predict_scam(payload))
    except RequestValidationError as exc:
        return _response(400, {"error": str(exc)})
    except Exception:
        return _response(500, {"error": "Inference failed"})
