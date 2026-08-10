"""
Fraud-Check consumer: polls the payment-events SQS queue, runs a fraud
decision on each PaymentCreated event, stores the result, and deletes
the message only after the result is safely committed. Runs as a
scheduled Lambda in AWS; invoked directly here for local testing.
"""

import json
import os

import boto3

from database import SessionLocal
from models import FraudCheck
from models import FraudCheck, FraudCheckEvent

SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
QUEUE_NAME = os.getenv("PAYMENT_EVENTS_QUEUE_NAME", "payment-events")
REVIEW_THRESHOLD = 1000

sqs = boto3.client(
    "sqs",
    endpoint_url=SQS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

_queue_url_cache = None


def get_queue_url() -> str:
    global _queue_url_cache
    if _queue_url_cache is None:
        _queue_url_cache = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    return _queue_url_cache


def assess_fraud(amount: float) -> tuple[str, float]:
    """
    Rules-based stub. Replace with a real model call (e.g. XGBoost
    propensity score) later -- everything else stays the same.
    """
    score = min(amount / REVIEW_THRESHOLD, 1.0)
    decision = "review" if amount > REVIEW_THRESHOLD else "approved"
    return decision, score


def process_message(db, message: dict) -> None:
    body = json.loads(message["Body"])
    payload = body["payload"]

    amount = float(payload["amount"])
    decision, score = assess_fraud(amount)

    fraud_check = FraudCheck(
        payment_id=body["payment_id"],
        idempotency_key=payload.get("idempotency_key"),
        amount=amount,
        currency=payload["currency"],
        decision=decision,
        score=score,
    )
    db.add(fraud_check)
    db.flush()  # assigns fraud_check.id without committing yet

    event = FraudCheckEvent(
        fraud_check_id=fraud_check.id,
        event_type="FraudCheckCompleted",
        payload={
            "payment_id": str(fraud_check.payment_id),
            "idempotency_key": fraud_check.idempotency_key,
            "amount": str(fraud_check.amount),
            "currency": fraud_check.currency,
            "decision": decision,
            "score": str(score),
        },
    )
    db.add(event)
    db.commit()

    # Only delete after both rows are safely committed together -- if
    # this process crashes before here, the message reappears after
    # the visibility timeout and gets retried.
    sqs.delete_message(
        QueueUrl=get_queue_url(),
        ReceiptHandle=message["ReceiptHandle"],
    )


def lambda_handler(event, context):
    response = sqs.receive_message(
        QueueUrl=get_queue_url(),
        MaxNumberOfMessages=10,
        WaitTimeSeconds=2,
    )
    messages = response.get("Messages", [])

    db = SessionLocal()
    processed = 0
    try:
        for message in messages:
            process_message(db, message)
            processed += 1
    finally:
        db.close()

    return {"processed_count": processed}


if __name__ == "__main__":
    result = lambda_handler({}, None)
    print(result)