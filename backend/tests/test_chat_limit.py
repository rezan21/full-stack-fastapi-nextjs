from datetime import UTC, datetime

import pytest
from sqlmodel import Session, col, select

from app.core import chat_limit
from app.core.chat_limit import TooManyRuns
from app.core.config import settings
from app.core.db import engine
from app.models import ChatUsage
from tests.utils.user import create_random_user

HOUR = datetime(2030, 1, 1, 10, 0, tzinfo=UTC)
LATER_IN_THE_HOUR = HOUR.replace(minute=20, second=30)
NEXT_HOUR = HOUR.replace(hour=11)


@pytest.fixture(autouse=True)
def three_runs_per_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CHAT_RUNS_PER_HOUR", 3)


def test_runs_are_allowed_up_to_the_quota_and_then_refused(db: Session) -> None:
    user = create_random_user(db)

    for _ in range(3):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(TooManyRuns):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)


def test_a_refused_run_is_not_counted(db: Session) -> None:
    user = create_random_user(db)
    for _ in range(3):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(TooManyRuns):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    usage = db.exec(select(ChatUsage).where(ChatUsage.user_id == user.id)).one()
    assert usage.runs == 3


def test_the_quota_is_per_user(db: Session) -> None:
    busy, idle = create_random_user(db), create_random_user(db)
    for _ in range(3):
        chat_limit.count_run(db, busy.id, LATER_IN_THE_HOUR)

    chat_limit.count_run(db, idle.id, LATER_IN_THE_HOUR)


def test_the_quota_is_shared_across_sessions(db: Session) -> None:
    user = create_random_user(db)
    for _ in range(2):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    with Session(engine) as other_worker:
        chat_limit.count_run(other_worker, user.id, LATER_IN_THE_HOUR)
        with pytest.raises(TooManyRuns):
            chat_limit.count_run(other_worker, user.id, LATER_IN_THE_HOUR)


def test_the_quota_starts_over_in_the_next_hour(db: Session) -> None:
    user = create_random_user(db)
    for _ in range(3):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    chat_limit.count_run(db, user.id, NEXT_HOUR)


def test_a_refusal_says_how_long_until_the_next_hour(db: Session) -> None:
    user = create_random_user(db)
    for _ in range(3):
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(TooManyRuns) as refused:
        chat_limit.count_run(db, user.id, LATER_IN_THE_HOUR)

    assert refused.value.retry_after == 39 * 60 + 30


def test_counts_from_past_hours_are_forgotten(db: Session) -> None:
    user = create_random_user(db)
    chat_limit.count_run(db, user.id, HOUR)

    chat_limit.count_run(db, user.id, NEXT_HOUR)

    windows = db.exec(
        select(ChatUsage.window_start).where(col(ChatUsage.user_id) == user.id)
    ).all()
    assert windows == [NEXT_HOUR]
