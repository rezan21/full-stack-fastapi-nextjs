from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import select
from tenacity import RetryError, stop_after_attempt, wait_none

from src.scripts.wait_for_db import init, logger, main


async def test_init_successful_connection() -> None:
    session = AsyncMock()
    select1 = select(1)

    with (
        patch("src.scripts.wait_for_db.AsyncSession") as session_class,
        patch("src.scripts.wait_for_db.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        session_class.return_value.__aenter__.return_value = session
        await init(MagicMock())

    session.exec.assert_awaited_once_with(select1)


async def test_init_logs_and_gives_up_when_the_database_is_unreachable() -> None:
    once = init.retry_with(stop=stop_after_attempt(1), wait=wait_none())
    with (
        patch("src.scripts.wait_for_db.AsyncSession", side_effect=RuntimeError("down")),
        patch.object(logger, "error") as log_error,
        pytest.raises(RetryError),
    ):
        await once(MagicMock())

    log_error.assert_called_once()


def test_main_waits_for_the_database() -> None:
    with patch("src.scripts.wait_for_db.init") as init_mock:
        main()

    init_mock.assert_called_once()
