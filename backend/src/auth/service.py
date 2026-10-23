import hashlib
import hmac
import logging
from datetime import timedelta
from math import ceil

from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.config import auth_settings
from src.auth.exceptions import (
    AccountInactive,
    AccountLocked,
    IncorrectLogin,
    IncorrectPassword,
    InvalidToken,
)
from src.auth.models import AuthThrottle
from src.auth.schemas import Token
from src.auth.utils import (
    create_access_token,
    generate_password_reset_token,
    get_password_hash,
    password_fingerprint,
    verify_password,
    verify_password_reset_token,
)
from src.config import settings
from src.models import get_datetime_utc
from src.notifications import service as notifications_service
from src.notifications.schemas import EmailData
from src.users import service as users_service
from src.users.models import User
from src.utils import describe_duration

DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"

logger = logging.getLogger(__name__)


def throttle_key(email: str) -> str:
    """Return the key under which an account's failed attempts are counted."""
    return hashlib.sha256(email.lower().encode()).hexdigest()


async def ensure_not_locked(session: AsyncSession, email: str) -> None:
    """Raise AccountLocked while the account is locked after too many failed attempts."""
    row = await session.get(AuthThrottle, throttle_key(email))
    now = get_datetime_utc()
    if row and row.lock_expires_at and row.lock_expires_at > now:
        raise AccountLocked(ceil((row.lock_expires_at - now).total_seconds()))


async def record_failure(session: AsyncSession, email: str) -> None:
    """Count a failed attempt and lock the account after too many."""
    now = get_datetime_utc()
    window = timedelta(minutes=auth_settings.AUTH_LOCK_MINUTES)
    key = throttle_key(email)
    await session.exec(
        delete(AuthThrottle).where(col(AuthThrottle.last_failure_at) < now - window)
    )
    await session.exec(
        insert(AuthThrottle)
        .values(key=key, failures=1, last_failure_at=now)
        .on_conflict_do_update(
            index_elements=[col(AuthThrottle.key)],
            set_={
                "failures": col(AuthThrottle.failures) + 1,
                "last_failure_at": now,
            },
        )
    )
    await session.exec(
        update(AuthThrottle)
        .where(
            col(AuthThrottle.key) == key,
            col(AuthThrottle.failures) >= auth_settings.AUTH_MAX_FAILURES,
        )
        .values(lock_expires_at=now + window)
    )
    await session.commit()


async def clear_failures(session: AsyncSession, email: str) -> None:
    """Forget the failed attempts of the account."""
    await session.exec(
        delete(AuthThrottle).where(col(AuthThrottle.key) == throttle_key(email))
    )
    await session.commit()


async def require_current_password(
    session: AsyncSession, user: User, password: str
) -> None:
    """Raise unless the password is the user's, counting failures against the account."""
    await ensure_not_locked(session, user.email)
    verified, _ = await run_in_threadpool(
        verify_password, password, user.hashed_password
    )
    if not verified:
        await record_failure(session, user.email)
        raise IncorrectPassword()
    await clear_failures(session, user.email)


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    """Return the user when the credentials are valid, otherwise None."""
    db_user = await users_service.get_user_by_email(session=session, email=email)
    if not db_user:
        await run_in_threadpool(verify_password, password, DUMMY_HASH)
        return None
    verified, updated_password_hash = await run_in_threadpool(
        verify_password, password, db_user.hashed_password
    )
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    return db_user


def issue_token(user: User) -> Token:
    """Create a login token for the user."""
    expires_delta = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(user.id, expires_delta, user.token_version),
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
    )


async def login(*, session: AsyncSession, email: str, password: str) -> Token:
    """Return a token for the credentials, counting failures against the account."""
    await ensure_not_locked(session, email)
    user = await authenticate(session=session, email=email, password=password)
    if not user:
        await record_failure(session, email)
        raise IncorrectLogin()
    await clear_failures(session, email)
    if not user.is_active:
        raise AccountInactive()
    return issue_token(user)


async def logout(session: AsyncSession, user: User) -> None:
    """Sign the user out everywhere by retiring their tokens."""
    users_service.revoke_tokens(user)
    session.add(user)
    await session.commit()


async def reset_password(session: AsyncSession, token: str, new_password: str) -> None:
    """Set a new password from a password reset token."""
    claims = verify_password_reset_token(token=token)
    if not claims:
        raise InvalidToken()
    email, fingerprint = claims
    user = await users_service.get_user_by_email(session=session, email=email)
    if not user or not hmac.compare_digest(
        password_fingerprint(user.hashed_password), fingerprint
    ):
        raise InvalidToken()
    if not user.is_active:
        raise AccountInactive()
    user.hashed_password = await run_in_threadpool(get_password_hash, new_password)
    users_service.revoke_tokens(user)
    session.add(user)
    await session.commit()
    await clear_failures(session, user.email)


async def request_password_recovery(
    *, session: AsyncSession, email: str, background_tasks: BackgroundTasks
) -> None:
    """Schedule a recovery email when the address has an account."""
    user = await users_service.get_user_by_email(session=session, email=email)
    if user:
        background_tasks.add_task(
            send_password_recovery_email,
            email_to=user.email,
            email=email,
            hashed_password=user.hashed_password,
        )


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """Build the password recovery email."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = notifications_service.render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_for": describe_duration(
                auth_settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            ),
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


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
        notifications_service.send_email(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    except Exception:
        logger.exception("Failed to send the password recovery email")
