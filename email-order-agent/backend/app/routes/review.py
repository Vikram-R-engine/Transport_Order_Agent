from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import EmailMessage, HumanReview, EmailStatus
from ..schemas import ReviewUpdateIn
from ..worker import process_email_task
from ..auth import require_role, get_current_user

router = APIRouter(prefix="/review", tags=["review"])

@router.get("/queue")
def review_queue(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # any logged in user can view
):
    emails = (
        db.query(EmailMessage)
        .filter(EmailMessage.status == EmailStatus.NEEDS_HUMAN_REVIEW)
        .order_by(EmailMessage.received_at.desc())
        .all()
    )
    return emails

@router.post("/{email_id}/submit")
def submit_review(
    email_id: int,
    payload: ReviewUpdateIn,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "reviewer"))  # only admin/reviewer can submit
):
    em = db.query(EmailMessage).get(email_id)
    if not em:
        raise HTTPException(status_code=404, detail="Email not found")

    em.extracted = {**(em.extracted or {}), **payload.proposed_fields}
    em.missing_fields = [k for k in (em.missing_fields or []) if k not in payload.proposed_fields]

    hr = db.query(HumanReview).filter(HumanReview.email_id == email_id).first()
    if not hr:
        hr = HumanReview(email_id=email_id)

    hr.proposed_fields = payload.proposed_fields
    hr.reviewer = payload.reviewer
    hr.approved = True

    em.status = EmailStatus.READY_TO_CONFIRM if len(em.missing_fields) == 0 else EmailStatus.NEEDS_HUMAN_REVIEW

    db.add(em)
    db.add(hr)
    db.commit()

    # If all fields are complete, continue pipeline
    if em.status == EmailStatus.READY_TO_CONFIRM:
        process_email_task.delay(email_id)

    return {"ok": True, "status": em.status, "missing_fields": em.missing_fields}