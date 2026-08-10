"""
Outbox relay: scans payment_events for unpublished rows, publishes them,
and marks them published. Runs as a scheduled Lambda in AWS (EventBridge
schedule triggers this handler); can also be invoked directly for local
testing without any AWS infra.
"""

from sqlalchemy.orm import Session

from database import SessionLocal
from models import PaymentEvent

BATCH_SIZE = 50


def publish_event(event: PaymentEvent) -> None:
    """
    Stub publisher. Swap this for a boto3 SQS/EventBridge call once the
    messaging infra exists -- isolating it here means the polling/marking
    logic below doesn't change when that happens.
    """
    print(f"Publishing event {event.id} ({event.event_type}) for payment {event.payment_id}")


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