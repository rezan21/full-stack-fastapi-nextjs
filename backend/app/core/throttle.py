import hashlib
from datetime import timedelta
from math import ceil

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, delete, update

from app.core.config import settings
from app.models import AuthThrottle, get_datetime_utc


class TooManyAttempts(Exception):
    """Raised while an account is locked after too many failed attempts."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"locked for {retry_after} more seconds")
        self.retry_after = retry_after


def throttle_key(email: str) -> str:
    """Return the key under which an account's failed attempts are counted."""
    return hashlib.sha256(email.lower().encode()).hexdigest()


def check(session: Session, email: str) -> None:
    """Raise TooManyAttempts while the account is locked."""
    row = session.get(AuthThrottle, throttle_key(email))
    now = get_datetime_utc()
    if row and row.locked_until and row.locked_until > now:
        raise TooManyAttempts(ceil((row.locked_until - now).total_seconds()))


def record_failure(session: Session, email: str) -> None:
    """Count a failed attempt and lock the account after too many."""
    now = get_datetime_utc()
    window = timedelta(minutes=settings.AUTH_LOCK_MINUTES)
    key = throttle_key(email)
    session.exec(
        delete(AuthThrottle).where(col(AuthThrottle.last_failure_at) < now - window)
    )
    session.exec(
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
    session.exec(
        update(AuthThrottle)
        .where(
            col(AuthThrottle.key) == key,
            col(AuthThrottle.failures) >= settings.AUTH_MAX_FAILURES,
        )
        .values(locked_until=now + window)
    )
    session.commit()


def clear(session: Session, email: str) -> None:
    """Forget the failed attempts of the account."""
    session.exec(
        delete(AuthThrottle).where(col(AuthThrottle.key) == throttle_key(email))
    )
    session.commit()
