import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal

from ag_ui.core import (
    BaseEvent,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunStartedEvent,
)
from ag_ui_langgraph import LangGraphAgent
from deepagents import create_deep_agent
from fastapi import FastAPI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr

from src.chat import constants as chat_constants
from src.chat.config import chat_settings
from src.chat.schemas import AgentMessage
from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Chat:
    checkpointer: BaseCheckpointSaver[Any]
    agent: LangGraphAgent | None


def build_agent(
    model: BaseChatModel, checkpointer: BaseCheckpointSaver[Any]
) -> LangGraphAgent:
    """Build the chat agent over the model, remembering conversations in the checkpointer."""
    graph = create_deep_agent(
        model=model,
        system_prompt=chat_constants.SYSTEM_PROMPT,
        checkpointer=checkpointer,
        name="chat",
    )
    return LangGraphAgent(
        name="chat",
        graph=graph,
        config={"recursion_limit": chat_constants.RECURSION_LIMIT},
        emit_raw_events=False,
    )


async def stream_events(
    agent: LangGraphAgent,
    run_input: RunAgentInput,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> AsyncIterator[BaseEvent]:
    """Stream a run's events, hiding the details of any failure from the client."""
    started = False
    try:
        async for event in agent.clone().run(run_input):
            started = started or event.type == EventType.RUN_STARTED
            if event.type == EventType.RUN_ERROR:
                yield event.model_copy(update={"message": chat_constants.GENERIC_ERROR})
                continue
            if event.type == EventType.RUN_FINISHED and on_finished:
                await on_finished()
            yield event
    except Exception:
        logger.exception("Chat run failed")
        if not started:
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=run_input.thread_id,
                run_id=run_input.run_id,
            )
        yield RunErrorEvent(
            type=EventType.RUN_ERROR, message=chat_constants.GENERIC_ERROR
        )


def agent_message(message: BaseMessage) -> AgentMessage | None:
    """Return the message as the user would read it, or None when it has no text for them."""
    role: Literal["user", "assistant"]
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    else:
        return None
    text = str(message.text)
    if message.id is None or not text.strip():
        return None
    return AgentMessage(id=message.id, role=role, content=text)


async def read_history(
    agent: LangGraphAgent, conversation_id: uuid.UUID
) -> list[AgentMessage]:
    """Return what the user and the assistant said, as the agent remembers it."""
    state = await agent.graph.aget_state(
        {"configurable": {"thread_id": str(conversation_id)}}
    )
    messages = (state.values or {}).get("messages", [])
    shown = (agent_message(message) for message in messages)
    return [message for message in shown if message is not None]


async def delete_threads(
    checkpointer: BaseCheckpointSaver[Any], conversation_ids: Iterable[uuid.UUID]
) -> None:
    """Forget everything stored for the conversations."""
    for conversation_id in conversation_ids:
        await checkpointer.adelete_thread(str(conversation_id))


def conninfo() -> str:
    """Return the database URL in the form psycopg takes."""
    return str(settings.DATABASE_URL).replace(
        "postgresql+psycopg://", "postgresql://", 1
    )


def build_model(api_key: SecretStr, name: str) -> ChatOpenAI:
    """Build the OpenAI chat model with bounded output, time and retries."""
    return ChatOpenAI(
        model=name,
        api_key=api_key,
        max_completion_tokens=chat_constants.MAX_OUTPUT_TOKENS,
        timeout=chat_constants.MODEL_TIMEOUT_SECONDS,
        max_retries=chat_constants.MODEL_MAX_RETRIES,
        use_responses_api=False,
        store=False,
    )


async def check_connection(connection: AsyncConnection[DictRow]) -> None:
    """Raise when a pooled connection has stopped working."""
    await connection.execute("")


@asynccontextmanager
async def chat_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the chat's database pool for the life of the app."""
    pool = AsyncConnectionPool[AsyncConnection[DictRow]](
        conninfo(),
        min_size=0,
        max_size=chat_constants.POOL_MAX_SIZE,
        open=False,
        check=check_connection,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await pool.open()
    try:
        checkpointer = AsyncPostgresSaver(pool)
        api_key = chat_settings.OPENAI_API_KEY
        agent = (
            build_agent(build_model(api_key, chat_settings.CHAT_MODEL), checkpointer)
            if api_key
            else None
        )
        app.state.chat = Chat(checkpointer=checkpointer, agent=agent)
        yield
    finally:
        await pool.close()
