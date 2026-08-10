import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReviewCase(Base):
    __tablename__ = "review_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    idempotency_key = Column(String, nullable=True)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=False)
    fraud_score = Column(Numeric, nullable=False)
    status = Column(String, nullable=False, default="pending_review")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReviewCaseEvent(Base):
    __tablename__ = "review_case_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_case_id = Column(UUID(as_uuid=True), ForeignKey("review_cases.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "ReviewCaseOpened"
    payload = Column(JSONB, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)