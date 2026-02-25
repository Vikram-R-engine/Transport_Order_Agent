from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import ExtractionRun, EmailMessage, Order
from ..auth import get_current_user

router = APIRouter(prefix="/activity", tags=["activity"])

@router.get("/recent")
def recent(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    runs = db.query(ExtractionRun).order_by(ExtractionRun.created_at.desc()).limit(20).all()
    emails = db.query(EmailMessage).order_by(EmailMessage.received_at.desc()).limit(10).all()
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()

    def run_row(r):
        return {
            "type": "extraction",
            "time": r.created_at.isoformat(),
            "layer": r.layer,
            "email_id": r.email_id,
            "missing": (r.output_snapshot or {}).get("missing", []),
        }

    def email_row(e):
        return {
            "type": "email",
            "time": e.received_at.isoformat(),
            "email_id": e.id,
            "from": e.from_email,
            "subject": e.subject,
            "status": e.status,
        }

    def order_row(o):
        return {
            "type": "order",
            "time": o.created_at.isoformat(),
            "job_id": o.job_id,
            "customer_name": o.customer_name,
            "weight_kg": o.weight_kg,
        }

    # Merge into one timeline (simple + clear)
    timeline = [*map(run_row, runs), *map(email_row, emails), *map(order_row, orders)]
    timeline.sort(key=lambda x: x["time"], reverse=True)
    return {"timeline": timeline[:30]}