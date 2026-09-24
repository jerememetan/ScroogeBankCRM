from get_churn_probability import lambda_handler

## This is the JSON
event = {
    "asOfDate": "2026-09-24",
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
            "counterpartyReference": None
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
        },
        {
            "id": "T1003",
            "accountId": "A5678",
            "clientId": "C1002",
            "transaction": "TRANSFER",
            "direction": "OUTGOING",
            "amount": 999.0,
            "date": "2026-09-20",
            "status": "FAILED",
            "balanceAfter": None,
            "counterpartyReference": "ACCOUNT-991"
        }
    ]
}

result = lambda_handler(event, None)
print(result)
