import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    idempotency_key = Column(String, nullable=True)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False, default="settled")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SettlementEvent(Base):
    __tablename__ = "settlement_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    settlement_id = Column(UUID(as_uuid=True), ForeignKey("settlements.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "SettlementCompleted"
    payload = Column(JSONB, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)