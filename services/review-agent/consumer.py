"""
Review-Agent consumer: polls fraud-check-events, processes only events
where decision == "review", opens a ReviewCase + ReviewCaseEvent
(outbox) atomically, deletes the message only after commit.

Current logic is intentionally a stub: it just records the case as
"pending_review". Planned evolution -- see README -- is an LLM/RAG
layer reasoning over FCA/CIFAS criteria to make an actual triage
decision instead of just parking every case.
"""

import json
import os

import boto3

from database import SessionLocal
from models import ReviewCase, ReviewCaseEvent

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

    if payload["decision"] != "review":
        sqs.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=message["ReceiptHandle"])
        return

    review_case = ReviewCase(
        payment_id=payload["payment_id"],
        idempotency_key=payload.get("idempotency_key"),
        amount=payload.get("amount", 0),
        currency=payload.get("currency", ""),
        fraud_score=payload.get("score", 0),
        status="pending_review",
    )
    db.add(review_case)
    db.flush()

    event = ReviewCaseEvent(
        review_case_id=review_case.id,
        event_type="ReviewCaseOpened",
        payload={
            "payment_id": str(review_case.payment_id),
            "idempotency_key": review_case.idempotency_key,
            "status": review_case.status,
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