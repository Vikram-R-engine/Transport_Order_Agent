from sqlalchemy.orm import Session
from datetime import datetime
import random
from .models import EmailMessage, Order, EmailStatus

def generate_job_id() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    rnd = random.randint(100000, 999999)
    return f"JOB-{stamp}-{rnd}"

def create_order_from_email(db: Session, email: EmailMessage) -> Order:
    data = email.extracted or {}

    order = Order(
        job_id=generate_job_id(),
        email_id=email.id,
        customer_name=str(data.get("customer_name", "")).strip(),
        weight_kg=int(float(data.get("weight_kg", 0) or 0)),
        pickup_location=str(data.get("pickup_location", "")).strip(),
        drop_location=str(data.get("drop_location", "")).strip(),
        pickup_time_window=str(data.get("pickup_time_window", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
    )
    db.add(order)
    email.status = EmailStatus.ORDER_CREATED
    db.add(email)
    db.commit()
    db.refresh(order)
    return order