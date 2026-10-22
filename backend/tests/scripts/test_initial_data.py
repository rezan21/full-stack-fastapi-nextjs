from unittest.mock import AsyncMock, patch

from src.scripts.initial_data import init, main


async def test_init_creates_the_initial_data_in_a_session() -> None:
    session = AsyncMock()
    with (
        patch("src.scripts.initial_data.SessionFactory") as session_factory,
        patch("src.scripts.initial_data.init_db") as init_db,
    ):
        session_factory.return_value.__aenter__.return_value = session
        await init()

    init_db.assert_awaited_once_with(session)


def test_main_creates_the_initial_data() -> None:
    with patch("src.scripts.initial_data.init") as init_mock:
        main()

    init_mock.assert_called_once()
