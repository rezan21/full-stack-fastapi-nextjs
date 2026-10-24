from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from ag_ui_langgraph import LangGraphAgent
from fastapi import FastAPI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from src.agent import factory as agent_factory
from src.agent.config import agent_settings
from src.config import settings

POOL_MAX_SIZE = 4


@dataclass
class AgentRuntime:
    checkpointer: BaseCheckpointSaver[Any]
    agent: LangGraphAgent | None


def conninfo() -> str:
    """Return the database URL in the form psycopg takes."""
    return str(settings.DATABASE_URL).replace(
        "postgresql+psycopg://", "postgresql://", 1
    )


async def check_connection(connection: AsyncConnection[DictRow]) -> None:
    """Raise when a pooled connection has stopped working."""
    await connection.execute("")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Open the agent's database pool for the life of the app."""
    pool = AsyncConnectionPool[AsyncConnection[DictRow]](
        conninfo(),
        min_size=0,
        max_size=POOL_MAX_SIZE,
        open=False,
        check=check_connection,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await pool.open()
    try:
        checkpointer = AsyncPostgresSaver(pool)
        api_key = agent_settings.OPENAI_API_KEY
        agent = (
            agent_factory.build_agent(
                agent_factory.build_model(api_key, agent_settings.CHAT_MODEL),
                checkpointer,
            )
            if api_key
            else None
        )
        app.state.agent_runtime = AgentRuntime(checkpointer=checkpointer, agent=agent)
        yield
    finally:
        await pool.close()
