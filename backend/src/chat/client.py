import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import aclosing, asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal

import anyio
from ag_ui.core import (
    BaseEvent,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunStartedEvent,
    TextMessageContentEvent,
)
from ag_ui_langgraph import LangGraphAgent
from deepagents import create_deep_agent
from fastapi import FastAPI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr

from src.chat.config import chat_settings
from src.chat.notes import NOTES_PROMPT, is_app_note, reply_failed, reply_stopped
from src.chat.schemas import AgentMessage
from src.config import settings

MAX_OUTPUT_TOKENS = 8192
MODEL_TIMEOUT_SECONDS = 60
MODEL_MAX_RETRIES = 2
POOL_MAX_SIZE = 4
RECURSION_LIMIT = 30
GENERIC_ERROR = "The assistant ran into a problem. Please try again."
SYSTEM_PROMPT = f"You are a helpful assistant. Keep answers concise. {NOTES_PROMPT}"

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
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        name="chat",
    )
    return LangGraphAgent(
        name="chat",
        graph=graph,
        config={"recursion_limit": RECURSION_LIMIT},
        emit_raw_events=False,
    )


async def stream_events(
    agent: LangGraphAgent,
    run_input: RunAgentInput,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> AsyncIterator[BaseEvent]:
    """Stream a run's events, hiding the details of any failure from the client."""
    started = False
    finished = False
    failed = False
    streamed: dict[str, str] = {}
    try:
        async with aclosing(agent.clone().run(run_input)) as events:
            async for event in events:
                started = started or event.type == EventType.RUN_STARTED
                if isinstance(event, TextMessageContentEvent):
                    text = streamed.get(event.message_id, "")
                    streamed[event.message_id] = text + event.delta
                if event.type == EventType.RUN_ERROR:
                    failed = True
                    yield event.model_copy(update={"message": GENERIC_ERROR})
                    continue
                if event.type == EventType.RUN_FINISHED:
                    finished = True
                    if on_finished:
                        await on_finished()
                yield event
    except Exception:
        logger.exception("Chat run failed")
        failed = True
        if not started:
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=run_input.thread_id,
                run_id=run_input.run_id,
            )
        yield RunErrorEvent(type=EventType.RUN_ERROR, message=GENERIC_ERROR)
    finally:
        if streamed and not finished:
            with anyio.CancelScope(shield=True):
                await settle_unfinished_run(
                    agent,
                    uuid.UUID(run_input.thread_id),
                    streamed,
                    reply_failed() if failed else reply_stopped(),
                    on_finished,
                )


async def settle_unfinished_run(
    agent: LangGraphAgent,
    conversation_id: uuid.UUID,
    streamed: dict[str, str],
    note: HumanMessage,
    on_finished: Callable[[], Awaitable[None]] | None,
) -> None:
    """Keep what an unfinished run streamed, in the agent's memory and the transcript."""
    try:
        await keep_streamed_text(agent, conversation_id, streamed, note)
        if on_finished:
            await on_finished()
    except Exception:
        logger.exception("Could not keep an unfinished reply")


async def keep_streamed_text(
    agent: LangGraphAgent,
    conversation_id: uuid.UUID,
    streamed: dict[str, str],
    note: HumanMessage,
) -> None:
    """Add the text a cut-off model call streamed to the agent's memory, followed by a note saying why it was cut off."""
    config = thread_config(conversation_id)
    state = await agent.graph.aget_state(config)
    remembered = {message.id for message in (state.values or {}).get("messages", [])}
    unsaved = [
        AIMessage(id=message_id, content=text)
        for message_id, text in streamed.items()
        if message_id not in remembered and text.strip()
    ]
    if unsaved and state.next:
        await agent.graph.aupdate_state(
            config, {"messages": [*unsaved, note]}, as_node=state.next[0]
        )


def thread_config(conversation_id: uuid.UUID) -> RunnableConfig:
    """Return the agent's config for a conversation's thread."""
    return {"configurable": {"thread_id": str(conversation_id)}}


def agent_message(message: BaseMessage) -> AgentMessage | None:
    """Return the message as the user would read it, or None when it has no text for them."""
    role: Literal["user", "assistant"]
    if is_app_note(message):
        return None
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
    state = await agent.graph.aget_state(thread_config(conversation_id))
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
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_MAX_RETRIES,
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
        max_size=POOL_MAX_SIZE,
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
