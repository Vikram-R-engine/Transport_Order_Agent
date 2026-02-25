from sqlalchemy.orm import Session
from .regex_layer import extract_with_regex
from .gemini_layer import extract_with_gemini
from ..models import EmailMessage, ExtractionRun, EmailStatus, Template
from ..config import settings

def run_extraction_pipeline(db: Session, email: EmailMessage) -> EmailMessage:
    email.status = EmailStatus.EXTRACTING
    email.last_error = ""
    db.add(email)
    db.commit()
    db.refresh(email)

    tpl = db.query(Template).filter(Template.active == True).first()
    patterns = tpl.patterns if tpl else None

    # Layer 1: Regex
    regex_data, missing = extract_with_regex(email.body_text or "", patterns=patterns)
    db.add(ExtractionRun(
        email_id=email.id,
        layer="regex",
        input_snapshot={"body": email.body_text},
        output_snapshot={"extracted": regex_data, "missing": missing},
    ))
    db.commit()

    # Layer 2: Gemini if missing
    if missing:
        merged, missing2 = extract_with_gemini(
            email_text=email.body_text or "",
            partial=regex_data,
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL
        )
        db.add(ExtractionRun(
            email_id=email.id,
            layer="gemini",
            input_snapshot={"partial": regex_data},
            output_snapshot={"extracted": merged, "missing": missing2},
        ))
        db.commit()

        email.extracted = merged
        email.missing_fields = missing2
        email.status = EmailStatus.NEEDS_HUMAN_REVIEW if missing2 else EmailStatus.READY_TO_CONFIRM
    else:
        email.extracted = regex_data
        email.missing_fields = []
        email.status = EmailStatus.READY_TO_CONFIRM

    db.add(email)
    db.commit()
    db.refresh(email)
    return email