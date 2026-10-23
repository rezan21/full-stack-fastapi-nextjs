import logging
import smtplib
import ssl
from pathlib import Path
from typing import Any

import emails
from jinja2 import Template

from src.config import settings
from src.notifications.config import notifications_settings
from src.utils import describe_duration

SMTP_TIMEOUT_SECONDS = 10
TEMPLATES_DIR = Path(__file__).parents[2] / "templates" / "email"

logger = logging.getLogger(__name__)


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """Render an email template with the context."""
    template_str = (TEMPLATES_DIR / template_name).read_text()
    html_content: str = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """Send an email."""
    assert notifications_settings.emails_enabled, (
        "no provided configuration for email variables"
    )
    assert notifications_settings.EMAILS_FROM_EMAIL
    assert notifications_settings.SMTP_HOST
    message = emails.message.Message(
        subject=subject,
        html=html_content,
        mail_from=(
            notifications_settings.EMAILS_FROM_NAME,
            notifications_settings.EMAILS_FROM_EMAIL,
        ),
    )
    message.mail_to = email_to
    context = ssl.create_default_context()
    timeout = SMTP_TIMEOUT_SECONDS
    if notifications_settings.SMTP_SSL and not notifications_settings.SMTP_TLS:
        server: smtplib.SMTP = smtplib.SMTP_SSL(
            notifications_settings.SMTP_HOST,
            notifications_settings.SMTP_PORT,
            timeout=timeout,
            context=context,
        )
    else:
        server = smtplib.SMTP(
            notifications_settings.SMTP_HOST,
            notifications_settings.SMTP_PORT,
            timeout=timeout,
        )
    with server:
        if notifications_settings.SMTP_TLS:
            server.starttls(context=context)
        if notifications_settings.SMTP_USER:
            server.login(
                notifications_settings.SMTP_USER,
                notifications_settings.SMTP_PASSWORD or "",
            )
        server.sendmail(
            notifications_settings.EMAILS_FROM_EMAIL, [email_to], message.as_string()
        )
    logger.info("Sent an email")


def send_confirmation_email(
    *,
    email_to: str,
    subject: str,
    message: str,
    path: str,
    token: str,
    valid_minutes: int,
) -> None:
    """Send an email with a link that confirms the address."""
    try:
        html_content = render_email_template(
            template_name="confirm_email.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email_to,
                "message": message,
                "valid_for": describe_duration(valid_minutes),
                "link": f"{settings.FRONTEND_HOST}{path}?token={token}",
            },
        )
        send_email(email_to=email_to, subject=subject, html_content=html_content)
    except Exception:
        logger.exception("Failed to send the confirmation email")


def send_notice_email(*, email_to: str, subject: str, message: str) -> None:
    """Send an email that tells the owner of an address about a security event."""
    try:
        html_content = render_email_template(
            template_name="notice.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email_to,
                "message": message,
            },
        )
        send_email(email_to=email_to, subject=subject, html_content=html_content)
    except Exception:
        logger.exception("Failed to send the notice email")
