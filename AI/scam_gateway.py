from get_scam_probability import lambda_handler

## This is the JSON
event = {
    "historyStartDate": "2026-09-01",
    "transaction": {
        "id": "T2001",
        "accountId": "A5678",
        "clientId": "C1002",
        "transaction": "TRANSFER",
        "direction": "OUTGOING",
        "amount": 1200.0,
        "date": "2026-09-24",
        "status": "PENDING",
        "balanceAfter": None,
        "counterpartyReference": "ACCOUNT-991"
    },
    "counterpartyHistoryDates": [
        "2026-09-20",
        "2026-09-21"
    ]
}

result = lambda_handler(event, None)
print(result)
