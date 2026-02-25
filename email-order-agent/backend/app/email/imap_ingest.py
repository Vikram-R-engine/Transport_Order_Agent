import imaplib, email
from email.header import decode_header
from typing import List, Dict

def fetch_unseen_emails(host: str, user: str, password: str, folder: str = "INBOX") -> List[Dict]:
    if not host or not user or not password:
        return []

    mail = imaplib.IMAP4_SSL(host)
    mail.login(user, password)
    mail.select(folder)

    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        mail.logout()
        return []

    results = []
    for num in messages[0].split():
        _, msg_data = mail.fetch(num, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        message_id = (msg.get("Message-ID", "") or "").strip()
        from_email = (msg.get("From", "") or "").strip()

        subject, enc = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(enc or "utf-8", errors="ignore")

        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get("Content-Disposition"))
                if ctype == "text/plain" and "attachment" not in disp:
                    body_text = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body_text = msg.get_payload(decode=True).decode(errors="ignore")

        results.append({
            "message_id": message_id or f"imap-{num.decode()}",
            "from_email": from_email,
            "subject": subject or "",
            "body_text": body_text or "",
        })

    mail.logout()
    return results