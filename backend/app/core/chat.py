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
    UserMessage,
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
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool

from app.core import transcript
from app.core.config import settings
from app.core.db import engine
from app.core.transcript import AgentMessage
from app.models import CONVERSATION_TITLE_MAX_LENGTH, MAX_MESSAGE_CHARS, ChatRun

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 8192
MODEL_TIMEOUT_SECONDS = 60
MODEL_MAX_RETRIES = 2
POOL_MAX_SIZE = 4
RECURSION_LIMIT = 30
RUN_ID_MAX_LENGTH = 100
GENERIC_ERROR = "The assistant ran into a problem. Please try again."
SYSTEM_PROMPT = "You are a helpful assistant. Keep answers concise."


class ChatInputError(ValueError):
    """Raised when a run request carries no usable user message."""


@dataclass
class Chat:
    checkpointer: BaseCheckpointSaver[Any]
    agent: LangGraphAgent | None


def newest_user_text(body: ChatRun) -> str:
    """Return the text of the newest user message in the request."""
    user_messages = [message for message in body.messages if message.role == "user"]
    if not user_messages:
        raise ChatInputError("The request has no user message")
    content = user_messages[-1].content
    if not isinstance(content, str) or not content.strip():
        raise ChatInputError("The message must be non-empty text")
    if len(content) > MAX_MESSAGE_CHARS:
        raise ChatInputError(f"The message is over {MAX_MESSAGE_CHARS} characters")
    return content


def conversation_title(text: str) -> str:
    """Return a conversation's title, taken from its first message."""
    return " ".join(text.split())[:CONVERSATION_TITLE_MAX_LENGTH]


def build_run_input(body: ChatRun, conversation_id: uuid.UUID) -> RunAgentInput:
    """Build a conversation's run from the newest user message, ignoring the rest."""
    text = newest_user_text(body)
    run_id = body.run_id if len(body.run_id) <= RUN_ID_MAX_LENGTH else str(uuid.uuid4())
    return RunAgentInput(
        thread_id=str(conversation_id),
        run_id=run_id,
        messages=[UserMessage(id=str(uuid.uuid4()), role="user", content=text)],
        state={},
        tools=[],
        context=[],
        forwarded_props={},
        resume=None,
    )


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
    try:
        async for event in agent.clone().run(run_input):
            started = started or event.type == EventType.RUN_STARTED
            if event.type == EventType.RUN_ERROR:
                yield event.model_copy(update={"message": GENERIC_ERROR})
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
        yield RunErrorEvent(type=EventType.RUN_ERROR, message=GENERIC_ERROR)


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


def replies_after(
    history: list[AgentMessage], user_message_id: str
) -> list[AgentMessage]:
    """Return what the assistant said after the user message with the id."""
    ids = [message.id for message in history]
    if user_message_id not in ids:
        logger.warning("A run's message is not in the agent's history")
        return []
    later = history[ids.index(user_message_id) + 1 :]
    return [message for message in later if message.role == "assistant"]


def save_replies(conversation_id: uuid.UUID, replies: list[AgentMessage]) -> None:
    """Add the replies to a conversation's transcript."""
    with Session(engine) as session:
        transcript.add_messages(session, conversation_id, replies)
        session.commit()


async def record_replies(agent: LangGraphAgent, run_input: RunAgentInput) -> None:
    """Add the assistant's answers to a run's message to the conversation's transcript."""
    conversation_id = uuid.UUID(run_input.thread_id)
    history = await read_history(agent, conversation_id)
    replies = replies_after(history, run_input.messages[0].id)
    await run_in_threadpool(save_replies, conversation_id, replies)


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
        api_key = settings.OPENAI_API_KEY
        agent = (
            build_agent(build_model(api_key, settings.CHAT_MODEL), checkpointer)
            if api_key
            else None
        )
        app.state.chat = Chat(checkpointer=checkpointer, agent=agent)
        yield
    finally:
        await pool.close()
