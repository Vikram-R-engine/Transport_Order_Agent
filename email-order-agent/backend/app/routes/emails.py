from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import EmailMessage
from ..schemas import EmailOut
from ..worker import process_email_task
from ..auth import get_current_user

router = APIRouter(prefix="/emails", tags=["emails"])

@router.get("", response_model=list[EmailOut])
def list_emails(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(EmailMessage).order_by(EmailMessage.received_at.desc()).limit(200).all()

@router.get("/{email_id}", response_model=EmailOut)
def get_email(email_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    em = db.query(EmailMessage).get(email_id)
    if not em:
        raise HTTPException(404, "Email not found")
    return em

@router.post("/{email_id}/process")
def process_email(email_id: int, user: str = Depends(get_current_user)):
    process_email_task.delay(email_id)
    return {"ok": True, "message": "Processing started"}