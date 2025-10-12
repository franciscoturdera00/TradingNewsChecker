import os
import smtplib
from dotenv import load_dotenv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base_reporter import BaseReporter

load_dotenv()

class EmailReporter(BaseReporter):
    """
    Send HTML + plaintext multipart emails. Usage:
        reporter.send_report(html_body, subject="Daily Portfolio Update", is_html=True)
    If is_html=True and no plaintext is provided, a minimal text fallback is auto-generated.
    """

    def send_report(self, report: str, *, subject: str | None = None, is_html: bool = False, plain_fallback: str | None = None):
        email_server = os.getenv("EMAIL_SERVER", "")
        email_port = os.getenv("EMAIL_PORT", "")
        email_username = os.getenv("EMAIL_USERNAME", "")
        email_password = os.getenv("EMAIL_PASSWORD", "")
        recipient_email = os.getenv("RECIPIENT_EMAIL", "")

        if any(x == "" for x in [email_server, email_port, email_username, email_password, recipient_email]):
            raise ValueError("Email configuration is incomplete. Please check environment variables.")

        try:
            email_port = int(email_port)
        except ValueError:
            raise ValueError("EMAIL_PORT must be a valid integer.")

        subject = subject or f"Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
        sender = email_username
        recipient = recipient_email

        if is_html:
            html_part = MIMEText(report, "html", "utf-8")
            # crude plaintext fallback if not provided
            if not plain_fallback:
                plain_fallback = "Your email client does not support HTML.\nOpen this email in a modern client to view the formatted report."
            text_part = MIMEText(plain_fallback, "plain", "utf-8")

            msg = MIMEMultipart("alternative")
            msg.attach(text_part)
            msg.attach(html_part)
        else:
            msg = MIMEText(report, "plain", "utf-8")

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        # Send
        with smtplib.SMTP(email_server, email_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            server.sendmail(sender, [recipient], msg.as_string())
