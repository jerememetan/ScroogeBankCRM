from get_scam_probability import lambda_handler

# This is a Python dictionary representing the JSON request body.
# Python comments are useful here for documentation, but comments must be
# removed when copying this object into an actual API Gateway JSON request.
event = {
    # Baseline date used to convert the transaction date into model time steps.
    "historyStartDate": "2026-09-01",

    "transaction": {
        # Unique identifier for this attempted transaction. Not a model feature.
        "id": "T2001",

        # Account from which the money is being withdrawn. Not a model feature.
        "accountId": "A5678",

        # Client associated with the account. Not a model feature.
        "clientId": "C1002",

        # CRM transaction type. WITHDRAWAL is converted to CASH_OUT for the model.
        "transaction": "WITHDRAWAL",

        # Money is leaving the account. This scorer only accepts OUTGOING events.
        "direction": "OUTGOING",

        # Amount that the client attempted to withdraw.
        "amount": 1200.0,

        # Date of the attempted withdrawal. With no stored time, midnight is used.
        "date": "2026-09-24",

        # The attempt failed. Status is validated but is not a model feature,
        # because failed attempts can still be useful for scam-risk review.
        "status": "FAILED",

        # Recorded balance after the attempt. The scorer accepts this value but
        # does not use it to infer direction or calculate the scam probability.
        # A failed transaction would commonly store this as None in production.
        "balanceAfter": 200.0,

        # Fictional destination/reference for gathering prior interaction dates.
        # The raw reference is not passed into the model.
        "counterpartyReference": "ACCOUNT-001"
    },

    # Earlier interactions with ACCOUNT-001. Only dates strictly before the
    # current transaction count. Here, prior count = 2 and destination age is
    # four days, which becomes 4 * 24 = 96 model steps.
    "counterpartyHistoryDates": [
        "2026-09-20",
        "2026-09-21"
    ]
}

# Direct Lambda-style invocation: pass the request object and no AWS context.
result = lambda_handler(event, None)
print(result)

# SAMPLE OUTPUT
#{'model': 'crm_scam_risk_xgboost',    - classifier info
# 'model_version': '2.0.0',            - classifier info
# 'classification': 'SCAM',            - classification SCAM/ NOT_SCAM
# 'is_positive': True,                 - True/ False
# 'probability': 0.889429,             - confidence score
# 'threshold': 0.2,                    - current threshold settings to classify as scam
# 'advisory_only': True,               - only display an alert, not a hard block to the transaction / do something
# 'transactionId': 'T2001',            - Just transaction info as usual
# 'accountId': 'A5678',
# 'clientId': 'C1002'}