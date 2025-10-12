import smtplib
import os
from dotenv import load_dotenv
from .base_reporter import BaseReporter
from datetime import datetime

load_dotenv()

class EmailReporter(BaseReporter):
    def send_report(self, report):
        email_server = os.getenv("EMAIL_SERVER", "")
        email_port = os.getenv("EMAIL_PORT", "")
        email_username = os.getenv("EMAIL_USERNAME", "")
        email_password = os.getenv("EMAIL_PASSWORD", "")
        recipient_email = os.getenv("RECIPIENT_EMAIL", "")

        if not all([email_server, email_port, email_username, email_password, recipient_email]):
            raise ValueError("Email configuration is incomplete. Please check environment variables.")

        try:
            email_port = int(email_port)
        except ValueError:
            raise ValueError("EMAIL_PORT must be a valid integer.")

        subject = f"Trading News Report - {datetime.now().strftime('%Y-%m-%d')}"
        body = report

        message = f"Subject: {subject}\n\n{body}"

        with smtplib.SMTP(email_server, email_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            server.sendmail(email_username, recipient_email, message)
