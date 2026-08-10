"""
Outbox relay: scans payment_events for unpublished rows, publishes them
to SQS, and marks them published. Runs as a scheduled Lambda in AWS
(EventBridge schedule triggers this handler); can also be invoked
directly for local testing against LocalStack.
"""

import json
import os

import boto3
from sqlalchemy.orm import Session

from database import SessionLocal
from models import PaymentEvent

BATCH_SIZE = 50
SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
QUEUE_NAME = os.getenv("PAYMENT_EVENTS_QUEUE_NAME", "payment-events")

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
        response = sqs.get_queue_url(QueueName=QUEUE_NAME)
        _queue_url_cache = response["QueueUrl"]
    return _queue_url_cache


def publish_event(event: PaymentEvent) -> None:
    sqs.send_message(
        QueueUrl=get_queue_url(),
        MessageBody=json.dumps(
            {
                "event_id": str(event.id),
                "payment_id": str(event.payment_id),
                "event_type": event.event_type,
                "payload": event.payload,
            }
        ),
    )


def relay_unpublished_events(db: Session) -> int:
    events = (
        db.query(PaymentEvent)
        .filter(PaymentEvent.published.is_(False))
        .order_by(PaymentEvent.created_at)
        .limit(BATCH_SIZE)
        .all()
    )

    published_count = 0
    for event in events:
        publish_event(event)
        event.published = True
        published_count += 1

    db.commit()
    return published_count


def lambda_handler(event, context):
    db = SessionLocal()
    try:
        count = relay_unpublished_events(db)
    finally:
        db.close()

    return {"published_count": count}


if __name__ == "__main__":
    result = lambda_handler({}, None)
    print(result)