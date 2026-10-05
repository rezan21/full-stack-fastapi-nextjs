import asyncio
import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.chat import conninfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup() -> None:
    """Create the tables the chat checkpointer keeps conversations in."""
    async with AsyncPostgresSaver.from_conn_string(conninfo()) as checkpointer:
        await checkpointer.setup()


def main() -> None:
    """Entry point for creating the chat tables."""
    logger.info("Creating chat tables")
    asyncio.run(setup())
    logger.info("Chat tables created")


if __name__ == "__main__":
    main()
