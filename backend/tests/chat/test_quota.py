from datetime import UTC, datetime

import pytest
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.chat import service as chat_service
from src.chat.config import chat_settings
from src.chat.exceptions import ChatQuotaExceeded
from src.chat.models import ChatUsage
from src.database import SessionFactory
from tests.utils.user import create_random_user

HOUR = datetime(2030, 1, 1, 10, 0, tzinfo=UTC)
LATER_IN_THE_HOUR = HOUR.replace(minute=20, second=30)
NEXT_HOUR = HOUR.replace(hour=11)


@pytest.fixture(autouse=True)
def three_runs_per_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat_settings, "CHAT_RUNS_PER_HOUR", 3)


async def test_runs_are_allowed_up_to_the_quota_and_then_refused(
    db: AsyncSession,
) -> None:
    user = await create_random_user(db)

    for _ in range(3):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(ChatQuotaExceeded):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)


async def test_a_refused_run_is_not_counted(db: AsyncSession) -> None:
    user = await create_random_user(db)
    for _ in range(3):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(ChatQuotaExceeded):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    usage = (
        await db.exec(select(ChatUsage).where(ChatUsage.owner_id == user.id))
    ).one()
    assert usage.runs == 3


async def test_the_quota_is_per_user(db: AsyncSession) -> None:
    busy, idle = await create_random_user(db), await create_random_user(db)
    for _ in range(3):
        await chat_service.count_run(db, busy.id, LATER_IN_THE_HOUR)

    await chat_service.count_run(db, idle.id, LATER_IN_THE_HOUR)


async def test_the_quota_is_shared_across_sessions(db: AsyncSession) -> None:
    user = await create_random_user(db)
    for _ in range(2):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    async with SessionFactory() as other_worker:
        await chat_service.count_run(other_worker, user.id, LATER_IN_THE_HOUR)
        with pytest.raises(ChatQuotaExceeded):
            await chat_service.count_run(other_worker, user.id, LATER_IN_THE_HOUR)


async def test_the_quota_starts_over_in_the_next_hour(db: AsyncSession) -> None:
    user = await create_random_user(db)
    for _ in range(3):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    await chat_service.count_run(db, user.id, NEXT_HOUR)


async def test_a_refusal_says_how_long_until_the_next_hour(db: AsyncSession) -> None:
    user = await create_random_user(db)
    for _ in range(3):
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    with pytest.raises(ChatQuotaExceeded) as refused:
        await chat_service.count_run(db, user.id, LATER_IN_THE_HOUR)

    assert refused.value.retry_after == 39 * 60 + 30


async def test_counts_from_past_hours_are_forgotten(db: AsyncSession) -> None:
    user = await create_random_user(db)
    await chat_service.count_run(db, user.id, HOUR)

    await chat_service.count_run(db, user.id, NEXT_HOUR)

    windows = (
        await db.exec(
            select(ChatUsage.window_started_at).where(
                col(ChatUsage.owner_id) == user.id
            )
        )
    ).all()
    assert windows == [NEXT_HOUR]
