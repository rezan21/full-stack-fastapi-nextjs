"""Creates the tables the agent keeps its threads in."""

import asyncio
import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agent import runtime as agent_runtime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup() -> None:
    """Create the tables the agent keeps its threads in."""
    async with AsyncPostgresSaver.from_conn_string(
        agent_runtime.conninfo()
    ) as checkpointer:
        await checkpointer.setup()


def main() -> None:
    """Entry point for creating the agent tables."""
    logger.info("Creating agent tables")
    asyncio.run(setup())
    logger.info("Agent tables created")


if __name__ == "__main__":
    main()
