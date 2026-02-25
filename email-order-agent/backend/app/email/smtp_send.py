import smtplib
from email.mime.text import MIMEText

def send_confirmation(
    smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str,
    from_addr: str, to_addr: str, subject: str, body: str
):
    if not smtp_host or not to_addr:
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_password)
        server.sendmail(from_addr, [to_addr], msg.as_string())