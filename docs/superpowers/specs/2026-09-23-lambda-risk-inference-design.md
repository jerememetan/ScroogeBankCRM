# Lambda Risk Inference Design

## Goal

Add two Python entry points that expose the downloaded Version 2 churn and scam XGBoost pipelines through both direct Lambda invocation and API Gateway proxy events. Callers provide CRM-oriented base fields; the functions construct the exact engineered feature rows expected by each fitted pipeline.

The scores are advisory. They may support creation of agent-review tickets but must not automatically block transactions, change customer records, or close accounts.

## Files

- `AI/get_churn_probability.py`
- `AI/get_scam_probability.py`
- `AI/models/crm_churn_pipeline.joblib`
- `AI/models/crm_churn_metadata.json`
- `AI/models/crm_scam_pipeline.joblib`
- `AI/models/crm_scam_metadata.json`
- `AI/tests/test_get_churn_probability.py`
- `AI/tests/test_get_scam_probability.py`

The two entry points remain independently deployable. Each owns its small amount of request parsing and validation rather than introducing a shared runtime module for only two functions.

## Invocation Modes

### Direct Lambda invocation

The event is the request object itself. A valid invocation returns the prediction object directly. Invalid direct invocations raise a `ValueError` with a caller-readable validation message.

### API Gateway proxy invocation

The event contains a JSON string in `body`. A valid request returns HTTP 200 with a JSON body. Validation errors return HTTP 400 with a JSON error body. Malformed JSON returns HTTP 400. Unexpected inference or artifact errors return HTTP 500 without exposing local paths or stack traces.

## Churn Request Contract

The churn request contains the non-engineered columns used to train the model:

```json
{
  "client_gender": "Female",
  "client_city": "Singapore",
  "account_branch_id": "SG-001",
  "client_tenure_months": 48,
  "client_age_years": 36,
  "account_current_balance": 8200.0,
  "account_previous_month_end_balance": 9000.0,
  "account_avg_balance_previous_quarter": 8800.0,
  "account_avg_balance_previous_two_quarters": 9100.0,
  "transaction_current_month_credit_total": 2400.0,
  "transaction_previous_month_credit_total": 3100.0,
  "transaction_current_month_debit_total": 3200.0,
  "transaction_previous_month_debit_total": 2100.0,
  "account_current_month_average_balance": 8500.0,
  "account_previous_month_average_balance": 9200.0,
  "transaction_days_since_last_activity": 18
}
```

The function derives:

- Current balance minus previous month-end balance.
- Current average balance minus previous average balance.
- Previous-quarter average minus previous-two-quarters average.
- Current and previous credit-minus-debit net flow.
- Current-minus-previous credit and debit changes.
- Current debit and credit totals divided by the absolute current balance with a small zero-safe denominator.

The constructed DataFrame is reordered to `feature_columns` from `crm_churn_metadata.json` before prediction.

## Scam Request Contract

```json
{
  "transaction_type": "TRANSFER",
  "transaction_amount": 1200.0,
  "transaction_date": "2026-09-23",
  "history_start_date": "2026-09-01",
  "destination_type": "ACCOUNT",
  "destination_history_dates": [
    "2026-09-20",
    "2026-09-21"
  ]
}
```

Accepted canonical transaction types are `CASH_IN`, `CASH_OUT`, `TRANSFER`, `PAYMENT`, and `DEBIT`. For compatibility with current mock records, `Deposit` normalizes to `CASH_IN` and `Withdrawal` normalizes to `CASH_OUT`. Other values are rejected rather than silently mapped to an unrelated type.

`destination_type` accepts `ACCOUNT` or `MERCHANT`.

Because the CRM stores dates without times, one day equals 24 model steps and the hour is consistently midnight:

- `transaction_day_index`: days from `history_start_date` to `transaction_date`.
- `transaction_hour_of_day`: `0`.
- `transaction_week_index`: day index divided by seven using integer division.
- `transaction_day_of_week`: day index modulo seven.
- `hour_sin`: `0`; `hour_cos`: `1`.
- `transaction_log_amount`: `log1p(transaction_amount)`.
- Type-specific amount columns: amount for the matching type and zero for other types.
- `destination_prior_count`: number of history dates strictly before the transaction date.
- `destination_prior_count_log`: `log1p(destination_prior_count)`.
- `destination_age_steps`: days since the earliest prior destination date, multiplied by 24; zero when no prior date exists.
- `destination_is_merchant`: one for `MERCHANT`, otherwise zero.

Future dates and dates equal to the current transaction date are not counted as prior history. The constructed DataFrame is reordered to `feature_columns` from `crm_scam_metadata.json` before prediction.

## Model Loading

Each module lazily loads its joblib pipeline and metadata from `AI/models` on the first invocation and caches them in module-level variables for Lambda warm-start reuse. Metadata supplies the threshold, version, model name, output-field name, and authoritative model feature order.

Loading is lazy so importing the module does not perform filesystem work and tests can exercise validation and feature construction independently.

## Prediction Response

Churn example:

```json
{
  "model": "crm_churn_xgboost",
  "model_version": "2.0.0",
  "classification": "CHURN",
  "is_positive": true,
  "probability": 0.7834,
  "threshold": 0.34,
  "advisory_only": true
}
```

The scam response uses `SCAM` or `NOT_SCAM`; the churn response uses `CHURN` or `NOT_CHURN`. Probability values are JSON numbers rounded to six decimal places. The unrounded value is used for the threshold comparison.

## Validation

- Required fields must be present; unexpected fields are tolerated so upstream contracts can evolve without breaking inference.
- Numeric fields must be finite numbers. Amounts, counts, ages, balances, and day differences that cannot logically be negative are rejected where applicable.
- Dates must use ISO `YYYY-MM-DD` format.
- `history_start_date` cannot be after `transaction_date`.
- Destination history must be a JSON list of ISO dates.
- Empty categorical strings and unsupported enum values are rejected.
- The generated feature columns must exactly cover the metadata contract before prediction.

## Testing

Tests are written before implementation and cover:

- Direct and API Gateway event parsing.
- Required-field and type validation.
- Exact churn engineered values.
- Exact scam date, history, cyclical, logarithmic, and type-amount values.
- Transaction alias normalization.
- Threshold-boundary classification.
- Metadata-driven feature ordering.
- One local smoke prediction against each real downloaded pipeline when compatible dependencies are available.

## Deployment Boundary

The initial deliverable is local Python code and tests. AWS deployment configuration, API Gateway resources, database queries, and automatic ticket creation are intentionally outside this change. The eventual Lambda package must use Python and dependency versions compatible with the Kaggle-exported scikit-learn and XGBoost artifacts; a Lambda container image is the preferred packaging route.
