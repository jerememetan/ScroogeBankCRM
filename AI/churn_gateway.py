from get_churn_probability import lambda_handler

# This is a Python dictionary representing the JSON request body.
# Python comments are useful here for documentation, but comments must be
# removed when copying this object into an actual API Gateway JSON request.
event = {
    # Snapshot date for the prediction. Age, tenure, transaction windows, and
    # days since last activity are all calculated relative to this date.
    "asOfDate": "2026-09-24",

    "client": {
        # Unique CRM client identifier. Returned for context, not used by the model.
        "clientId": "C1002",

        # Client characteristics used as model features.
        "gender": "Male",
        "city": "Singapore",

        # Used with asOfDate to calculate the client's completed age in years.
        "dateOfBirth": "2000-07-22"
    },

    "account": {
        # Unique account identifier. Returned for context, not used by the model.
        "accountId": "A5678",

        # Must match client.clientId so the account belongs to this client.
        "clientId": "C1002",

        # Account type and status are CRM context and are not model features.
        "accountType": "Checking",
        "accountStatus": "Active",

        # Used with asOfDate to calculate account tenure in completed months.
        "openingDate": "2018-09-01",

        # Opening-day starting balance before replaying completed transactions.
        "initialDeposit": 5000.0,

        # This project accepts SGD accounts only. Currency is not a model feature.
        "currency": "SGD",

        # Branch identifier is one of the categorical model features.
        "branchId": "SG-001"
    },

    # Transaction history used to derive balances, monthly credits/debits,
    # average daily balances, net flows, and days since the latest activity.
    "transactions": [
        {
            # Completed incoming deposit: adds 2,400 to the ledger balance and
            # contributes to the current month's credit total.
            "id": "T1001",
            "accountId": "A5678",
            "clientId": "C1002",
            "transaction": "DEPOSIT",
            "direction": "INCOMING",
            "amount": 2400.0,
            "date": "2020-09-05",
            "status": "COMPLETED",

            # Informational CRM snapshot; the scorer reconstructs the balance
            # from initialDeposit, direction, amount, date, and status instead.
            "balanceAfter": 7400.0,
            "counterpartyReference": None
        },
        {
            # Completed outgoing payment: subtracts 800 from the ledger balance
            # and contributes to the current month's debit total.
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
        },
        # {
        #     # Completed outgoing payment: transfer money to other banks (sign of churn?)
        #     "id": "T1002",
        #     "accountId": "A5678",
        #     "clientId": "C1002",
        #     "transaction": "DEBIT",
        #     "direction": "OUTGOING",
        #     "amount": 6600.0,
        #     "date": "2026-09-11",
        #     "status": "COMPLETED",
        #     "balanceAfter": 0,
        #     "counterpartyReference": None
        # },
        {
            # Failed outgoing transfer: retained as CRM history, but ignored by
            # churn balance and activity calculations because it did not complete.
            "id": "T1003",
            "accountId": "A5678",
            "clientId": "C1002",
            "transaction": "TRANSFER",
            "direction": "OUTGOING",
            "amount": 999.0,
            "date": "2026-09-20",
            "status": "FAILED",
            "balanceAfter": 6600.0,
            "counterpartyReference": "ACCOUNT-991"
        }
    ]
}

# Direct Lambda-style invocation: pass the request object and no AWS context.
result = lambda_handler(event, None)
print(result)
# SAMPLE OUTPUT
#{'model': 'crm_churn_xgboost',     - Classifier info 
# 'model_version': '2.0.0',         - Classifier info
# 'classification': 'NOT_CHURN',    - classification CHURN / NOT_CHURN
# 'is_positive': False,             - whether Churn is True/ False
# 'probability': 0.133507,          - Confidence score
# 'threshold': 0.34,                - Threshold to differciate CHURN/ NOT CHURN
# 'advisory_only': True,            - Only display an alert, not a hard block to the transaction / do something
# 'clientId': 'C1002',             - Info on client
# 'accountId': 'A5678'}