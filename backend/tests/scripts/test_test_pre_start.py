from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select
from tenacity import RetryError, stop_after_attempt, wait_none

from app.tests_pre_start import init, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.tests_pre_start.Session", return_value=session_mock),
        patch("app.tests_pre_start.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert connection_successful, (
            "The database connection should be successful and not raise an exception."
        )

        session_mock.exec.assert_called_once_with(select1)


def test_init_logs_and_gives_up_when_the_database_is_unreachable() -> None:
    once = init.retry_with(stop=stop_after_attempt(1), wait=wait_none())
    with (
        patch("app.tests_pre_start.Session", side_effect=RuntimeError("down")),
        patch.object(logger, "error") as log_error,
        pytest.raises(RetryError),
    ):
        once(MagicMock())

    log_error.assert_called_once()


def test_main_waits_for_the_database() -> None:
    with patch("app.tests_pre_start.init") as init_mock:
        main()

    init_mock.assert_called_once()
