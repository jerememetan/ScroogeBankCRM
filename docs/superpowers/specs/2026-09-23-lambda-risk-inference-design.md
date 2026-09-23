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

The churn request contains client and account fields from the application schema plus the account's completed transaction history:

```json
{
  "asOfDate": "2026-09-23",
  "client": {
    "clientId": "C1002",
    "gender": "Female",
    "city": "Singapore",
    "dateOfBirth": "1990-07-22"
  },
  "account": {
    "accountId": "A5678",
    "clientId": "C1002",
    "accountType": "Checking",
    "accountStatus": "Active",
    "openingDate": "2022-09-01",
    "initialDeposit": 5000.0,
    "currency": "SGD",
    "branchId": "SG-001"
  },
  "transactions": [
    {
      "id": "T1001",
      "accountId": "A5678",
      "clientId": "C1002",
      "transaction": "DEPOSIT",
      "direction": "INCOMING",
      "amount": 2400.0,
      "date": "2026-09-05",
      "status": "COMPLETED",
      "balanceAfter": 7400.0,
      "counterpartyReference": null
    },
    {
      "id": "T1002",
      "accountId": "A5678",
      "clientId": "C1002",
      "transaction": "PAYMENT",
      "direction": "OUTGOING",
      "amount": 800.0,
      "date": "2026-09-10",
      "status": "COMPLETED",
      "balanceAfter": 6600.0,
      "counterpartyReference": "MERCHANT-042"
    }
  ]
}
```

The function derives:

- Client age from `client.dateOfBirth` and `asOfDate`.
- Account tenure in completed months from `account.openingDate` and `asOfDate`.
- Model `account_branch_id` from `account.branchId`.
- The current balance by applying completed incoming and outgoing transactions to the initial deposit.
- Previous month-end balance by replaying completed transactions through that date.
- Current and previous calendar-month credit and debit totals.
- Current month-to-date and previous-calendar-month mean daily closing balances.
- The previous completed quarter's mean daily closing balance and the preceding quarter's mean daily closing balance.
- Days since the latest completed transaction.
- Current balance minus previous month-end balance.
- Current average balance minus previous average balance.
- Previous-quarter average minus the preceding-quarter average.
- Current and previous credit-minus-debit net flow.
- Current-minus-previous credit and debit changes.
- Current debit and credit totals divided by the absolute current balance with a small zero-safe denominator.

Only `COMPLETED` transactions on or before `asOfDate` affect the ledger. Incoming transactions are credits and outgoing transactions are debits. Transactions dated before the opening date are rejected. The initial deposit is the opening-day starting balance. With date-only records, all transactions on a date are reflected in that day's closing balance. Each transaction's `accountId` and `clientId` must match the enclosing account and client. `direction` is required regardless of transaction status and is never inferred from `balanceAfter`.

`account.currency` must be `SGD` for this project but is not a model feature. Account ID, client ID, account type, and account status are retained as response context but are not passed to the model. The constructed DataFrame is reordered to `feature_columns` from `crm_churn_metadata.json` before prediction.

## Scam Request Contract

```json
{
  "historyStartDate": "2026-09-01",
  "transaction": {
    "id": "T2001",
    "accountId": "A5678",
    "clientId": "C1002",
    "transaction": "TRANSFER",
    "direction": "OUTGOING",
    "amount": 1200.0,
    "date": "2026-09-23",
    "status": "PENDING",
    "balanceAfter": null,
    "counterpartyReference": "ACCOUNT-991"
  },
  "counterpartyHistoryDates": [
    "2026-09-20",
    "2026-09-21"
  ]
}
```

Accepted application transaction types are `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `PAYMENT`, and `DEBIT`. `DEPOSIT` normalizes to model value `CASH_IN`, and `WITHDRAWAL` normalizes to `CASH_OUT`. Other values are rejected rather than silently mapped to an unrelated type.

The initial scam scorer handles outgoing transactions, for which `counterpartyReference` represents the model destination. Incoming transaction records remain valid CRM records but are rejected by this scorer because the trained destination-history features would have different semantics. `counterpartyReference` is required for `TRANSFER` and `PAYMENT`. A payment counterparty is treated as a merchant; other supported outgoing transaction types are treated as non-merchant destinations.

Because the CRM stores dates without times, one day equals 24 model steps and the hour is consistently midnight:

- `transaction_day_index`: days from `historyStartDate` to `transaction.date`.
- `transaction_hour_of_day`: `0`.
- `transaction_week_index`: day index divided by seven using integer division.
- `transaction_day_of_week`: day index modulo seven.
- `hour_sin`: `0`; `hour_cos`: `1`.
- `transaction_log_amount`: `log1p(transaction.amount)`.
- Type-specific amount columns: amount for the matching type and zero for other types.
- `destination_prior_count`: number of `counterpartyHistoryDates` strictly before the transaction date.
- `destination_prior_count_log`: `log1p(destination_prior_count)`.
- `destination_age_steps`: days since the earliest prior destination date, multiplied by 24; zero when no prior date exists.
- `destination_is_merchant`: one for `PAYMENT`, otherwise zero.

Future dates and dates equal to the current transaction date are not counted as prior history. `direction` is required even for pending and failed transactions. The constructed DataFrame is reordered to `feature_columns` from `crm_scam_metadata.json` before prediction.

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
- `historyStartDate` cannot be after `transaction.date`.
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
