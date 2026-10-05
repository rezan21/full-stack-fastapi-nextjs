import uuid
from datetime import datetime, timedelta
from math import ceil

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, delete

from app.core.config import settings
from app.models import ChatUsage, get_datetime_utc

WINDOW = timedelta(hours=1)


class TooManyRuns(Exception):
    """Raised when a user has used up their chat runs for the hour."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"quota used up for {retry_after} more seconds")
        self.retry_after = retry_after


def window_start(now: datetime) -> datetime:
    """Return the start of the hour the time falls in."""
    return now.replace(minute=0, second=0, microsecond=0)


def count_run(
    session: Session, user_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Count a chat run, raising TooManyRuns once the hourly quota is used up."""
    now = now or get_datetime_utc()
    start = window_start(now)
    session.exec(delete(ChatUsage).where(col(ChatUsage.window_start) < start))
    counted = session.exec(
        insert(ChatUsage)
        .values(user_id=user_id, window_start=start, runs=1)
        .on_conflict_do_update(
            index_elements=[col(ChatUsage.user_id), col(ChatUsage.window_start)],
            set_={"runs": col(ChatUsage.runs) + 1},
            where=col(ChatUsage.runs) < settings.CHAT_RUNS_PER_HOUR,
        )
        .returning(col(ChatUsage.runs))
    ).first()
    session.commit()
    if counted is None:
        raise TooManyRuns(ceil((start + WINDOW - now).total_seconds()))
