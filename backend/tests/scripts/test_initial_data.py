from unittest.mock import MagicMock, patch

from app.initial_data import init, main


def test_init_creates_the_initial_data_in_a_session() -> None:
    session = MagicMock()
    with (
        patch("app.initial_data.Session") as session_class,
        patch("app.initial_data.init_db") as init_db,
    ):
        session_class.return_value.__enter__.return_value = session
        init()

    init_db.assert_called_once_with(session)


def test_main_creates_the_initial_data() -> None:
    with patch("app.initial_data.init") as init_mock:
        main()

    init_mock.assert_called_once()
