import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FraudCheck(Base):
    __tablename__ = "fraud_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    idempotency_key = Column(String, nullable=True)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=False)
    decision = Column(String, nullable=False)  # "approved" or "review"
    score = Column(Numeric, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FraudCheckEvent(Base):
    __tablename__ = "fraud_check_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fraud_check_id = Column(UUID(as_uuid=True), ForeignKey("fraud_checks.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "FraudCheckCompleted"
    payload = Column(JSONB, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)