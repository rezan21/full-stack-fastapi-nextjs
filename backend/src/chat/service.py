import logging
import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from math import ceil
from typing import Any

from ag_ui.core import ResumeEntry, RunAgentInput, Tool, ToolMessage, UserMessage
from ag_ui_langgraph import LangGraphAgent
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import browser as agent_browser
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from src.agent.schemas import AgentMessage
from src.chat.config import chat_settings
from src.chat.exceptions import (
    AnswerWithMessage,
    ChatQuotaExceeded,
    ConversationNotFound,
    EmptyMessage,
    InvalidToolResult,
    MessageTooLong,
    NoOpenInterrupt,
    NoPendingToolCall,
    NoUserMessage,
)
from src.chat.models import (
    CONVERSATION_TITLE_MAX_LENGTH,
    ChatMessage,
    ChatUsage,
    Conversation,
)
from src.chat.schemas import MAX_MESSAGE_CHARS, MAX_TOOL_RESULT_CHARS, ChatRun
from src.database import SessionFactory
from src.models import get_datetime_utc
from src.pagination import Pagination

QUOTA_WINDOW = timedelta(hours=1)

logger = logging.getLogger(__name__)


async def get_owned_conversation(
    session: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    """Return the conversation when it belongs to the user, or raise a 404."""
    conversation = (
        await session.exec(
            select(Conversation).where(
                col(Conversation.id) == conversation_id,
                col(Conversation.owner_id) == user_id,
            )
        )
    ).first()
    if not conversation:
        raise ConversationNotFound()
    return conversation


async def create_conversation(
    session: AsyncSession, owner_id: uuid.UUID
) -> Conversation:
    """Start a conversation for the user."""
    conversation = Conversation(owner_id=owner_id)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def list_conversations(
    session: AsyncSession, owner_id: uuid.UUID, pagination: Pagination
) -> tuple[Sequence[Conversation], int]:
    """Return a page of the user's conversations, latest activity first, and how many there are in all."""
    owned = col(Conversation.owner_id) == owner_id
    count = (
        await session.exec(select(func.count()).select_from(Conversation).where(owned))
    ).one()
    result = await session.exec(
        select(Conversation)
        .where(owned)
        .order_by(col(Conversation.updated_at).desc(), col(Conversation.id))
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.all(), count


async def delete_user_threads(
    session: AsyncSession, user_id: uuid.UUID, checkpointer: BaseCheckpointSaver[Any]
) -> None:
    """Forget what the agent remembers of every conversation of the user."""
    result = await session.exec(
        select(Conversation.id).where(col(Conversation.owner_id) == user_id)
    )
    await agent_threads.delete_threads(
        checkpointer, [str(conversation_id) for conversation_id in result.all()]
    )


def newest_user_text(body: ChatRun) -> str:
    """Return the text of the newest user message in the request."""
    user_messages = [message for message in body.messages if message.role == "user"]
    if not user_messages:
        raise NoUserMessage()
    content = user_messages[-1].content
    if not isinstance(content, str) or not content.strip():
        raise EmptyMessage()
    if len(content) > MAX_MESSAGE_CHARS:
        raise MessageTooLong(MAX_MESSAGE_CHARS)
    return content


def conversation_title(text: str) -> str:
    """Return a conversation's title, taken from its first message."""
    return " ".join(text.split())[:CONVERSATION_TITLE_MAX_LENGTH]


def message_id(agent_message_id: str) -> uuid.UUID:
    """Return the agent's message id as a UUID when it is one, or a new UUID."""
    try:
        return uuid.UUID(agent_message_id)
    except ValueError:
        return uuid.uuid4()


async def add_messages(
    session: AsyncSession, conversation_id: uuid.UUID, messages: Iterable[AgentMessage]
) -> None:
    """Add messages to a conversation's transcript, skipping any it already holds."""
    for message in messages:
        await session.exec(
            insert(ChatMessage)
            .values(
                id=message_id(message.id),
                conversation_id=conversation_id,
                agent_message_id=message.id,
                role=message.role,
                content=message.content,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    col(ChatMessage.conversation_id),
                    col(ChatMessage.agent_message_id),
                ]
            )
        )


async def read_messages(
    session: AsyncSession, conversation_id: uuid.UUID, limit: int
) -> tuple[list[ChatMessage], int]:
    """Return the latest messages of a conversation in order, and how many it holds."""
    in_conversation = col(ChatMessage.conversation_id) == conversation_id
    count = (
        await session.exec(
            select(func.count()).select_from(ChatMessage).where(in_conversation)
        )
    ).one()
    latest = await session.exec(
        select(ChatMessage)
        .where(in_conversation)
        .order_by(col(ChatMessage.seq).desc())
        .limit(limit)
    )
    return list(reversed(latest.all())), count


def window_start(now: datetime) -> datetime:
    """Return the start of the hour the time falls in."""
    return now.replace(minute=0, second=0, microsecond=0)


async def count_run(
    session: AsyncSession, owner_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Count a chat run, raising ChatQuotaExceeded once the hourly quota is used up."""
    now = now or get_datetime_utc()
    start = window_start(now)
    await session.exec(
        delete(ChatUsage).where(col(ChatUsage.window_started_at) < start)
    )
    counted = (
        await session.exec(
            insert(ChatUsage)
            .values(owner_id=owner_id, window_started_at=start, runs=1)
            .on_conflict_do_update(
                index_elements=[
                    col(ChatUsage.owner_id),
                    col(ChatUsage.window_started_at),
                ],
                set_={"runs": col(ChatUsage.runs) + 1},
                where=col(ChatUsage.runs) < chat_settings.CHAT_RUNS_PER_HOUR,
            )
            .returning(col(ChatUsage.runs))
        )
    ).first()
    await session.commit()
    if counted is None:
        raise ChatQuotaExceeded(ceil((start + QUOTA_WINDOW - now).total_seconds()))


async def count_turn(session: AsyncSession, conversation: Conversation) -> None:
    """Count a run that continues a conversation and mark the conversation as just used."""
    await count_run(session, conversation.owner_id)
    conversation.updated_at = get_datetime_utc()
    session.add(conversation)
    await session.commit()


async def start_run(
    session: AsyncSession,
    conversation: Conversation,
    body: ChatRun,
    agent: LangGraphAgent,
) -> RunAgentInput:
    """Count a run against the owner's quota, returning the agent's input."""
    tools = agent_browser.offered(tool.name for tool in body.tools)
    if body.messages and body.messages[-1].role == "tool":
        if body.resume:
            raise AnswerWithMessage()
        return await start_tool_result_run(session, conversation, body, agent, tools)
    if is_answer(body):
        return await start_answer_run(session, conversation, body, agent, tools)
    if any(entry.status == "resolved" for entry in body.resume):
        raise AnswerWithMessage()
    return await start_message_run(session, conversation, body, agent, tools)


def is_answer(body: ChatRun) -> bool:
    """Return whether the request answers what the assistant asked, with no new message from the user."""
    newest = body.messages[-1] if body.messages else None
    return bool(body.resume) and (newest is None or newest.role != "user")


async def start_message_run(
    session: AsyncSession,
    conversation: Conversation,
    body: ChatRun,
    agent: LangGraphAgent,
    tools: list[Tool],
) -> RunAgentInput:
    """Store the user's message of a run, returning the agent's input."""
    text = newest_user_text(body)
    await count_run(session, conversation.owner_id)
    await agent_threads.cancel_pending_calls(agent, str(conversation.id))
    message = UserMessage(id=str(uuid.uuid4()), role="user", content=text)
    await add_messages(
        session,
        conversation.id,
        [AgentMessage(id=message.id, role="user", content=text)],
    )
    conversation.updated_at = get_datetime_utc()
    if conversation.title is None:
        conversation.title = conversation_title(text)
    session.add(conversation)
    await session.commit()
    return agent_streaming.build_run_input(
        str(conversation.id), body.run_id, [message], tools
    )


async def start_tool_result_run(
    session: AsyncSession,
    conversation: Conversation,
    body: ChatRun,
    agent: LangGraphAgent,
    tools: list[Tool],
) -> RunAgentInput:
    """Return the input of a run that hands the agent what a browser tool answered."""
    message = body.messages[-1]
    content = message.content
    if not isinstance(content, str) or len(content) > MAX_TOOL_RESULT_CHARS:
        raise InvalidToolResult(MAX_TOOL_RESULT_CHARS)
    pending = await agent_threads.pending_tool_call_ids(agent, str(conversation.id))
    if message.tool_call_id not in pending:
        raise NoPendingToolCall()
    await count_turn(session, conversation)
    result = ToolMessage(
        id=str(uuid.uuid4()),
        role="tool",
        content=content,
        tool_call_id=message.tool_call_id,
    )
    return agent_streaming.build_run_input(
        str(conversation.id), body.run_id, [result], tools
    )


async def start_answer_run(
    session: AsyncSession,
    conversation: Conversation,
    body: ChatRun,
    agent: LangGraphAgent,
    tools: list[Tool],
) -> RunAgentInput:
    """Return the input of a run that hands the agent the user's answers to its open interrupts."""
    thread_id = str(conversation.id)
    waiting = {
        interrupt.interrupt_id
        for interrupt in await agent_threads.open_interrupts(agent, thread_id)
    }
    if sorted(entry.interrupt_id for entry in body.resume) != sorted(waiting):
        raise NoOpenInterrupt()
    await count_turn(session, conversation)
    answers = [
        ResumeEntry(
            interrupt_id=entry.interrupt_id,
            status=entry.status,
            payload=entry.payload,
        )
        for entry in body.resume
    ]
    return agent_streaming.build_run_input(thread_id, body.run_id, [], tools, answers)


def replies_after(
    history: list[AgentMessage], user_message_id: str | None
) -> list[AgentMessage]:
    """Return what the assistant said after the user message with the id."""
    ids = [message.id for message in history]
    if user_message_id not in ids:
        logger.warning("A run's message is not in the agent's history")
        return []
    later = history[ids.index(user_message_id) + 1 :]
    return [message for message in later if message.role == "assistant"]


async def save_replies(conversation_id: uuid.UUID, replies: list[AgentMessage]) -> None:
    """Add the replies to a conversation's transcript."""
    async with SessionFactory() as session:
        await add_messages(session, conversation_id, replies)
        await session.commit()


def answered_message_id(
    run_input: RunAgentInput, history: list[AgentMessage]
) -> str | None:
    """Return the id of the user message the run answers, which a tool result run takes from the history."""
    first = run_input.messages[0] if run_input.messages else None
    if first and first.role == "user":
        return first.id
    users = [message for message in history if message.role == "user"]
    return users[-1].id if users else None


async def record_replies(agent: LangGraphAgent, run_input: RunAgentInput) -> None:
    """Add the assistant's answers to a run's message to the conversation's transcript."""
    conversation_id = uuid.UUID(run_input.thread_id)
    history = await agent_threads.read_history(agent, run_input.thread_id)
    replies = replies_after(history, answered_message_id(run_input, history))
    await save_replies(conversation_id, replies)
