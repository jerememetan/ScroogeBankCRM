# Local Risk Gateway Scripts Design

## Goal

Provide clearly named local scripts for manually exercising the scam and churn Lambda handlers.

## Files

- Rename `AI/gateway.py` to `AI/scam_gateway.py` without changing its working scam request.
- Create `AI/churn_gateway.py` with a complete fictional CRM client, account, and transaction history.
- Do not modify either probability handler or model artifact.

## Behavior

Each script imports its corresponding `lambda_handler`, invokes it directly with a Python dictionary, and prints the prediction. The churn sample uses matching client/account identifiers, SGD currency, valid transaction directions, and completed plus failed transactions so the ledger logic is exercised.

## Verification

Run both scripts with the project Python 3.11 environment. Each must exit successfully and print a model response containing a probability and classification.
