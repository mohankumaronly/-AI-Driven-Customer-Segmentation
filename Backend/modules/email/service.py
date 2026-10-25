import os
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from flask import current_app, render_template

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def _send_via_brevo_api(api_key: str, sender_email: str, sender_name: str, to_email: str, subject: str, html_content: str) -> bool:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        }
        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in (200, 201, 202):
            logger.info("Email sent via Brevo API to %s", to_email)
            return True
        logger.warning("Brevo API failed with status %d: %s", response.status_code, response.text)
        return False

    @staticmethod
    def _send_via_brevo_smtp(sender_email: str, password: str, sender_name: str, to_email: str, subject: str, html_content: str) -> bool:
        smtp_server = "smtp-relay.brevo.com"
        port = 587
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port, timeout=10) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
        logger.info("Email sent via Brevo SMTP to %s", to_email)
        return True

    @classmethod
    def send_email(cls, to_email: str, subject: str, html_content: str) -> bool:
        config = current_app.config
        api_key = config.get("BREVO_API_KEY", "")
        sender_email = config.get("BREVO_SENDER_EMAIL", "noreply@example.com")
        sender_name = config.get("BREVO_SENDER_NAME", "AI Customer Segmentation")
        is_debug = config.get("DEBUG", False) or config.get("TESTING", False)

        if not api_key:
            logger.warning("BREVO_API_KEY not configured. Email to %s skipped.", to_email)
            return is_debug

        sent = False
        # If API key starts with xsmtpsib-, it is a Brevo SMTP key
        if api_key.startswith("xsmtpsib-"):
            try:
                sent = cls._send_via_brevo_smtp(sender_email, api_key, sender_name, to_email, subject, html_content)
            except Exception as e:
                logger.error("Error sending email via Brevo SMTP to %s: %s", to_email, e)
        else:
            try:
                sent = cls._send_via_brevo_api(api_key, sender_email, sender_name, to_email, subject, html_content)
            except Exception as e:
                logger.error("Error sending email via Brevo API: %s", e)
            
            if not sent:
                # Try fallback to SMTP if possible
                try:
                    sent = cls._send_via_brevo_smtp(sender_email, api_key, sender_name, to_email, subject, html_content)
                except Exception as e:
                    logger.error("Fallback Brevo SMTP also failed: %s", e)

        if not sent and is_debug:
            logger.warning("[DEV MODE] Email delivery failed or skipped for %s. Continuing in debug mode.", to_email)
            return True

        return sent

    @classmethod
    def send_verification_otp(cls, to_email: str, otp: str) -> bool:
        subject = "Verify your email address"
        html_content = render_template("verification.html", otp=otp)
        if current_app.config.get("DEBUG"):
            print(f"\n[DEV LOG] Verification OTP for {to_email}: {otp}\n", flush=True)
        return cls.send_email(to_email, subject, html_content)

    @classmethod
    def send_password_reset_otp(cls, to_email: str, otp: str) -> bool:
        subject = "Reset your password"
        html_content = render_template("password_reset.html", otp=otp)
        if current_app.config.get("DEBUG"):
            print(f"\n[DEV LOG] Password Reset OTP for {to_email}: {otp}\n", flush=True)
        return cls.send_email(to_email, subject, html_content)

    @classmethod
    def send_password_changed_notification(cls, to_email: str) -> bool:
        subject = "Security Alert: Password Changed"
        html_content = render_template("password_changed.html")
        return cls.send_email(to_email, subject, html_content)
