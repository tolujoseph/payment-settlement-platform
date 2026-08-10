from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Payment, PaymentEvent
from schemas import PaymentCreate, PaymentResponse

app = FastAPI(title="Payment Intake Service")


@app.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payment_in: PaymentCreate, db: Session = Depends(get_db)):
    existing = db.query(Payment).filter(
        Payment.idempotency_key == payment_in.idempotency_key
    ).first()
    if existing:
        return existing

    payment = Payment(
        idempotency_key=payment_in.idempotency_key,
        amount=payment_in.amount,
        currency=payment_in.currency,
    )
    db.add(payment)
    db.flush()  # assigns payment.id without committing yet

    event = PaymentEvent(
        payment_id=payment.id,
        event_type="PaymentCreated",
        payload={
            "payment_id": str(payment.id),
            "idempotency_key": payment.idempotency_key,
            "amount": str(payment.amount),
            "currency": payment.currency,
        },
    )
    db.add(event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Payment).filter(
            Payment.idempotency_key == payment_in.idempotency_key
        ).first()
        if existing:
            return existing
        raise HTTPException(status_code=500, detail="Failed to create payment")

    db.refresh(payment)
    return payment