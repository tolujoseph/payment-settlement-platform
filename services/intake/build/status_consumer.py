"""
Consumes FraudCheckCompleted events from the fraud-check-events queue
and updates the matching Payment's status. Runs as a scheduled Lambda
in AWS; invoked directly here for local testing.
"""

import json
import os

import boto3

from database import SessionLocal
from models import Payment

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

    payment = db.query(Payment).filter(Payment.id == payload["payment_id"]).first()
    if payment is None:
        sqs.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=message["ReceiptHandle"])
        return

    payment.status = payload["decision"]
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