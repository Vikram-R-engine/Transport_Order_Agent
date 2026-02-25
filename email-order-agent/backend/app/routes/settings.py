from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..config import settings
from ..auth import require_role
from ..email.imap_ingest import fetch_unseen_emails
from ..email.smtp_send import send_confirmation

router = APIRouter(prefix="/settings", tags=["settings"])

def masked(v: str) -> str:
    if not v:
        return ""
    if len(v) <= 4:
        return "*" * len(v)
    return v[:2] + "*" * (len(v) - 4) + v[-2:]

@router.get("/status")
def status(user=Depends(require_role("admin"))):
    imap_ok = bool(settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD)
    smtp_ok = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD and settings.SMTP_FROM)
    gemini_ok = bool(settings.GEMINI_API_KEY)

    return {
        "imap": {
            "ok": imap_ok,
            "host": settings.IMAP_HOST,
            "user": settings.IMAP_USER,
            "folder": settings.IMAP_FOLDER,
            "password_set": bool(settings.IMAP_PASSWORD),
        },
        "smtp": {
            "ok": smtp_ok,
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "from": settings.SMTP_FROM,
            "password_set": bool(settings.SMTP_PASSWORD),
        },
        "gemini": {
            "ok": gemini_ok,
            "model": settings.GEMINI_MODEL,
            "api_key_set": bool(settings.GEMINI_API_KEY),
        },
        "env_masked": {
            "IMAP_PASSWORD": masked(settings.IMAP_PASSWORD),
            "SMTP_PASSWORD": masked(settings.SMTP_PASSWORD),
            "GEMINI_API_KEY": masked(settings.GEMINI_API_KEY),
            "JWT_SECRET": masked(settings.JWT_SECRET),
        }
    }

@router.post("/test-imap")
def test_imap(user=Depends(require_role("admin"))):
    # Just try connecting and listing unseen count
    items = fetch_unseen_emails(settings.IMAP_HOST, settings.IMAP_USER, settings.IMAP_PASSWORD, settings.IMAP_FOLDER)
    return {"ok": True, "unseen_found": len(items)}

@router.post("/test-smtp")
def test_smtp(user=Depends(require_role("admin"))):
    # Sends test mail to SMTP_USER (self-test)
    to = settings.SMTP_USER
    send_confirmation(
        settings.SMTP_HOST, settings.SMTP_PORT,
        settings.SMTP_USER, settings.SMTP_PASSWORD,
        settings.SMTP_FROM,
        to_addr=to,
        subject="SMTP Test: Email Order Agent",
        body="SMTP Test OK. This is a connectivity test from the Email Order Agent dashboard."
    )
    return {"ok": True, "sent_to": to}

@router.post("/test-gemini")
def test_gemini(user=Depends(require_role("admin"))):
    if not settings.GEMINI_API_KEY:
        return {"ok": False, "error": "GEMINI_API_KEY is empty"}

    # Minimal smoke test without changing your extraction pipeline
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    resp = model.generate_content("Reply with one word: OK")
    return {"ok": True, "response": (resp.text or "").strip()}