import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    idempotency_key: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)


class PaymentResponse(BaseModel):
    id: uuid.UUID
    idempotency_key: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True