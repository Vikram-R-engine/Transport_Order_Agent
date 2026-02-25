from celery import Celery
from sqlalchemy.orm import Session
from .config import settings
from .db import SessionLocal
from .models import EmailMessage, EmailStatus, AgentState
from .email.imap_ingest import fetch_unseen_emails
from .extraction.pipeline import run_extraction_pipeline
from .crud import create_order_from_email
from .email.smtp_send import send_confirmation

celery_app = Celery("agent", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Periodic tick every 15 seconds
celery_app.conf.beat_schedule = {
    "agent-tick-every-15-seconds": {
        "task": "app.worker.agent_tick",
        "schedule": 15.0,
    }
}

@celery_app.task
def ingest_emails_task():
    items = fetch_unseen_emails(
        settings.IMAP_HOST,
        settings.IMAP_USER,
        settings.IMAP_PASSWORD,
        settings.IMAP_FOLDER
    )
    db: Session = SessionLocal()
    try:
        created = 0
        for it in items:
            exists = db.query(EmailMessage).filter(EmailMessage.message_id == it["message_id"]).first()
            if exists:
                continue
            em = EmailMessage(**it)
            db.add(em)
            db.commit()
            created += 1
        return f"Inserted {created} emails"
    finally:
        db.close()

@celery_app.task
def process_email_task(email_id: int):
    db: Session = SessionLocal()
    try:
        em = db.query(EmailMessage).get(email_id)
        if not em:
            return "Email not found"

        try:
            em = run_extraction_pipeline(db, em)
        except Exception as e:
            em.status = EmailStatus.FAILED
            em.last_error = str(e)
            db.add(em)
            db.commit()
            return f"Extraction failed: {e}"

        if em.status == EmailStatus.READY_TO_CONFIRM:
            order = create_order_from_email(db, em)

            body = f"""Hello,

We extracted the following shipment details from your email:

Customer Name: {order.customer_name}
Weight (kg): {order.weight_kg}
Pickup: {order.pickup_location}
Drop: {order.drop_location}
Pickup Time Window: {order.pickup_time_window}

Your Job ID is: {order.job_id}

Please reply to confirm or mention corrections.

Thanks,
Logistics Automation Agent
"""
            try:
                send_confirmation(
                    settings.SMTP_HOST, settings.SMTP_PORT,
                    settings.SMTP_USER, settings.SMTP_PASSWORD,
                    settings.SMTP_FROM,
                    em.from_email,
                    subject=f"Reconfirmation: Job {order.job_id}",
                    body=body
                )
                em.status = EmailStatus.CONFIRMATION_SENT
                db.add(em)
                db.commit()
                return f"Order created & confirmation sent: {order.job_id}"
            except Exception as e:
                em.last_error = f"SMTP error: {e}"
                db.add(em)
                db.commit()
                return f"Order created but email failed: {order.job_id}"

        return f"Email status: {em.status}"
    finally:
        db.close()

@celery_app.task(name="app.worker.agent_tick")
def agent_tick():
    db: Session = SessionLocal()
    try:
        st = db.query(AgentState).first()
        if not st or not st.enabled:
            return "Agent disabled"

        # Ingest unseen emails
        ingest_emails_task()

        # Queue processing for newly received/failed emails
        pending = db.query(EmailMessage).filter(
            EmailMessage.status.in_([EmailStatus.RECEIVED, EmailStatus.FAILED])
        ).order_by(EmailMessage.received_at.asc()).limit(10).all()

        for em in pending:
            process_email_task.delay(em.id)

        return f"Tick ok. queued={len(pending)}"
    finally:
        db.close()