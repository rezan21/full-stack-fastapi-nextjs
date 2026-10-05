import hashlib
import logging
import smtplib
import ssl
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import emails
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PASSWORD_RESET_AUDIENCE = "password-reset"
SIGNUP_AUDIENCE = "signup"
EMAIL_CHANGE_AUDIENCE = "email-change"
SMTP_TIMEOUT_SECONDS = 10
SECRET_FIELDS = [
    "new_password",
    "current_password",
    "access_token",
    "messages",
    "content",
]


@dataclass
class EmailData:
    html_content: str
    subject: str


def event_scrubber() -> EventScrubber:
    """Build the Sentry scrubber that also hides the password and token fields."""
    return EventScrubber(denylist=[*DEFAULT_DENYLIST, *SECRET_FIELDS], recursive=True)


def describe_duration(minutes: int) -> str:
    """Describe a duration in minutes for an email."""
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hour{'' if hours == 1 else 's'}"
    return f"{minutes} minute{'' if minutes == 1 else 's'}"


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
    assert settings.SMTP_HOST
    message = emails.message.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    message.mail_to = email_to
    context = ssl.create_default_context()
    if settings.SMTP_SSL and not settings.SMTP_TLS:
        server: smtplib.SMTP = smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=SMTP_TIMEOUT_SECONDS,
            context=context,
        )
    else:
        server = smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS
        )
    with server:
        if settings.SMTP_TLS:
            server.starttls(context=context)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        server.sendmail(settings.EMAILS_FROM_EMAIL, [email_to], message.as_string())
    logger.info("Sent an email")


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
            "valid_for": describe_duration(
                settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            ),
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def password_fingerprint(hashed_password: str) -> str:
    """Return a short digest of a password hash."""
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def generate_email_token(
    *, audience: str, claims: dict[str, str], expires_in: timedelta
) -> str:
    """Create a signed, expiring token for an emailed link."""
    now = datetime.now(UTC)
    return jwt.encode(
        {**claims, "aud": audience, "nbf": now, "exp": now + expires_in},
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


def generate_password_reset_token(email: str, hashed_password: str) -> str:
    """Create a password reset token for the email."""
    return generate_email_token(
        audience=PASSWORD_RESET_AUDIENCE,
        claims={"sub": email, "pwd": password_fingerprint(hashed_password)},
        expires_in=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )


def verify_password_reset_token(token: str) -> tuple[str, str] | None:
    """Return the email and password fingerprint in a valid reset token, otherwise None."""
    claims = verify_email_token(token, audience=PASSWORD_RESET_AUDIENCE)
    if not claims or "sub" not in claims or "pwd" not in claims:
        return None
    return str(claims["sub"]), str(claims["pwd"])


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


def send_signup_email(*, email_to: str, full_name: str) -> None:
    """Send the link that completes a sign-up."""
    token = generate_email_token(
        audience=SIGNUP_AUDIENCE,
        claims={"sub": email_to, "name": full_name},
        expires_in=timedelta(minutes=settings.SIGNUP_TOKEN_EXPIRE_MINUTES),
    )
    send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your email",
        message=f"Confirm your email address to finish creating your {settings.PROJECT_NAME} account:",
        path="/signup/complete",
        token=token,
        valid_minutes=settings.SIGNUP_TOKEN_EXPIRE_MINUTES,
    )


def send_email_change_email(
    *, email_to: str, user_id: uuid.UUID, current_email: str
) -> None:
    """Send the link that confirms a new email address."""
    token = generate_email_token(
        audience=EMAIL_CHANGE_AUDIENCE,
        claims={"sub": str(user_id), "email": email_to, "from": current_email},
        expires_in=timedelta(minutes=settings.EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES),
    )
    send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your new email",
        message=f"Confirm this address to use it for your {settings.PROJECT_NAME} account:",
        path="/confirm-email",
        token=token,
        valid_minutes=settings.EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES,
    )


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


def send_email_change_requested_notice(*, email_to: str, new_email: str) -> None:
    """Tell the current address that a change to a new address was requested."""
    send_notice_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Email change requested",
        message=(
            f"A change of the email address of your {settings.PROJECT_NAME} account "
            f"to {new_email} was requested. If this was you, confirm it from the "
            "link we sent to that address. If it was not, change your password now."
        ),
    )


def send_email_changed_notice(*, email_to: str, new_email: str) -> None:
    """Tell the previous address that the account now uses a new address."""
    send_notice_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Your email was changed",
        message=(
            f"The email address of your {settings.PROJECT_NAME} account was changed "
            f"to {new_email}, and every session was signed out. If this was not you, "
            "your account may be compromised: contact the site operator."
        ),
    )
