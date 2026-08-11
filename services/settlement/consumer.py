"""
Settlement consumer: polls fraud-check-events, processes only events
where decision == "approved", writes a Settlement + SettlementEvent
(outbox) in one transaction, and deletes the message only after commit.
"""

import json
import os

import boto3

from database import SessionLocal
from models import Settlement, SettlementEvent

SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL") or None
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
QUEUE_NAME = os.getenv("FRAUD_CHECK_EVENTS_QUEUE_NAME", "fraud-check-events")

sqs = boto3.client(
    "sqs",
    endpoint_url=SQS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id="test" if SQS_ENDPOINT_URL else None,
    aws_secret_access_key="test" if SQS_ENDPOINT_URL else None,
)

_queue_url_cache = None


def get_queue_url() -> str:
    global _queue_url_cache
    if _queue_url_cache is None:
        _queue_url_cache = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    return _queue_url_cache


def process_message(db, message: dict) -> None:
    body = json.loads(message["Body"])
    payload = body["payload"]

    if payload["decision"] != "approved":
        sqs.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=message["ReceiptHandle"])
        return

    settlement = Settlement(
        payment_id=payload["payment_id"],
        idempotency_key=payload.get("idempotency_key"),
        amount=payload.get("amount", 0),
        currency=payload.get("currency", ""),
        status="settled",
    )
    db.add(settlement)
    db.flush()

    event = SettlementEvent(
        settlement_id=settlement.id,
        event_type="SettlementCompleted",
        payload={
            "payment_id": str(settlement.payment_id),
            "idempotency_key": settlement.idempotency_key,
            "status": settlement.status,
        },
    )
    db.add(event)
    db.commit()

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