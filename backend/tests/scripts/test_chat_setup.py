import asyncio
from unittest.mock import patch

from sqlmodel import Session, text

from app.chat_setup import main, setup
from app.core.db import engine


def checkpoint_tables() -> set[str]:
    with Session(engine) as session:
        rows = session.exec(
            text(
                "select tablename from pg_tables "
                "where schemaname = 'public' and tablename like 'checkpoint%'"
            )
        )
        return {row[0] for row in rows}


def test_setup_creates_the_checkpoint_tables_and_can_run_again() -> None:
    asyncio.run(setup())
    asyncio.run(setup())

    assert {"checkpoints", "checkpoint_blobs", "checkpoint_writes"} <= (
        checkpoint_tables()
    )


def test_main_creates_the_chat_tables() -> None:
    with patch("app.chat_setup.setup") as setup_mock:
        main()

    setup_mock.assert_called_once()
