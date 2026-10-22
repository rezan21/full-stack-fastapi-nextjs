from unittest.mock import patch

from sqlmodel import text

from src.database import SessionFactory
from src.scripts.chat_setup import main, setup


async def checkpoint_tables() -> set[str]:
    async with SessionFactory() as session:
        rows = await session.exec(
            text(
                "select tablename from pg_tables "
                "where schemaname = 'public' and tablename like 'checkpoint%'"
            )
        )
        return {row[0] for row in rows}


async def test_setup_creates_the_checkpoint_tables_and_can_run_again() -> None:
    await setup()
    await setup()

    assert {"checkpoints", "checkpoint_blobs", "checkpoint_writes"} <= (
        await checkpoint_tables()
    )


def test_main_creates_the_chat_tables() -> None:
    with patch("src.scripts.chat_setup.setup") as setup_mock:
        main()

    setup_mock.assert_called_once()
