import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import emails
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SIGNUP_AUDIENCE = "signup"
EMAIL_CHANGE_AUDIENCE = "email-change"


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """Render an email template with the context."""
    template_str = (
        Path(__file__).parent / "email-templates" / template_name
    ).read_text()
    html_content: str = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """Send an email."""
    assert settings.emails_enabled, "no provided configuration for email variables"
    assert settings.EMAILS_FROM_EMAIL
    message = emails.message.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options: dict[str, Any] = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "fail_silently": False,
    }
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """Build the password recovery email."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def password_fingerprint(hashed_password: str) -> str:
    """Return a short digest of a password hash."""
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def generate_password_reset_token(email: str, hashed_password: str) -> str:
    """Create a password reset token for the email."""
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {
            "exp": exp,
            "nbf": now,
            "sub": email,
            "pwd": password_fingerprint(hashed_password),
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def send_password_recovery_email(
    *, email_to: str, email: str, hashed_password: str
) -> None:
    """Send the password recovery email."""
    try:
        token = generate_password_reset_token(
            email=email, hashed_password=hashed_password
        )
        email_data = generate_reset_password_email(
            email_to=email_to, email=email, token=token
        )
        send_email(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    except Exception:
        logger.exception("Failed to send the password recovery email")


def generate_email_token(*, audience: str, claims: dict[str, str]) -> str:
    """Create a signed, expiring token for an emailed link."""
    now = datetime.now(UTC)
    return jwt.encode(
        {
            **claims,
            "aud": audience,
            "nbf": now,
            "exp": now + timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS),
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )


def verify_email_token(token: str, *, audience: str) -> dict[str, Any] | None:
    """Return the claims of a valid token for the audience, otherwise None."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],
            audience=audience,
        )
    except InvalidTokenError:
        return None


def send_confirmation_email(
    *, email_to: str, subject: str, message: str, path: str, token: str
) -> None:
    """Send an email with a link that confirms the address."""
    try:
        html_content = render_email_template(
            template_name="confirm_email.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email_to,
                "message": message,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": f"{settings.FRONTEND_HOST}{path}?token={token}",
            },
        )
        send_email(email_to=email_to, subject=subject, html_content=html_content)
    except Exception:
        logger.exception("Failed to send the confirmation email")


def send_signup_email(*, email_to: str, full_name: str) -> None:
    """Send the link that completes a sign-up."""
    token = generate_email_token(
        audience=SIGNUP_AUDIENCE, claims={"sub": email_to, "name": full_name}
    )
    send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your email",
        message=f"Confirm your email address to finish creating your {settings.PROJECT_NAME} account:",
        path="/signup/complete",
        token=token,
    )


def send_email_change_email(
    *, email_to: str, user_id: uuid.UUID, current_email: str
) -> None:
    """Send the link that confirms a new email address."""
    token = generate_email_token(
        audience=EMAIL_CHANGE_AUDIENCE,
        claims={"sub": str(user_id), "email": email_to, "from": current_email},
    )
    send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your new email",
        message=f"Confirm this address to use it for your {settings.PROJECT_NAME} account:",
        path="/confirm-email",
        token=token,
    )


def verify_password_reset_token(token: str) -> tuple[str, str] | None:
    """Return the email and password fingerprint in a valid reset token, otherwise None."""
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"]), str(decoded_token["pwd"])
    except InvalidTokenError, KeyError:
        return None
