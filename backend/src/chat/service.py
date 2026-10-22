import logging
import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime
from math import ceil
from typing import Any

from ag_ui.core import RunAgentInput, UserMessage
from ag_ui_langgraph import LangGraphAgent
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.chat import client as chat_client
from src.chat import constants as chat_constants
from src.chat.config import chat_settings
from src.chat.constants import ErrorCode
from src.chat.exceptions import (
    ChatQuotaExceeded,
    ConversationNotFound,
    InvalidChatInput,
)
from src.chat.models import ChatMessage, ChatUsage, Conversation
from src.chat.schemas import AgentMessage, ChatRun
from src.database import SessionFactory
from src.models import get_datetime_utc
from src.pagination import Pagination

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
    await chat_client.delete_threads(checkpointer, result.all())


def newest_user_text(body: ChatRun) -> str:
    """Return the text of the newest user message in the request."""
    user_messages = [message for message in body.messages if message.role == "user"]
    if not user_messages:
        raise InvalidChatInput(ErrorCode.NO_USER_MESSAGE)
    content = user_messages[-1].content
    if not isinstance(content, str) or not content.strip():
        raise InvalidChatInput(ErrorCode.EMPTY_MESSAGE)
    if len(content) > chat_constants.MAX_MESSAGE_CHARS:
        raise InvalidChatInput(
            ErrorCode.MESSAGE_TOO_LONG.format(limit=chat_constants.MAX_MESSAGE_CHARS)
        )
    return content


def conversation_title(text: str) -> str:
    """Return a conversation's title, taken from its first message."""
    return " ".join(text.split())[: chat_constants.CONVERSATION_TITLE_MAX_LENGTH]


def build_run_input(body: ChatRun, conversation_id: uuid.UUID) -> RunAgentInput:
    """Build a conversation's run from the newest user message, ignoring the rest."""
    text = newest_user_text(body)
    run_id = (
        body.run_id
        if len(body.run_id) <= chat_constants.RUN_ID_MAX_LENGTH
        else str(uuid.uuid4())
    )
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
        raise ChatQuotaExceeded(
            ceil((start + chat_constants.QUOTA_WINDOW - now).total_seconds())
        )


async def start_run(
    session: AsyncSession, conversation: Conversation, body: ChatRun
) -> RunAgentInput:
    """Count a run against the owner's quota and store its user message, returning the agent's input."""
    run_input = build_run_input(body, conversation.id)
    await count_run(session, conversation.owner_id)
    message = run_input.messages[0]
    await add_messages(
        session,
        conversation.id,
        [AgentMessage(id=message.id, role="user", content=str(message.content))],
    )
    conversation.updated_at = get_datetime_utc()
    if conversation.title is None:
        conversation.title = conversation_title(str(message.content))
    session.add(conversation)
    await session.commit()
    return run_input


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


async def save_replies(conversation_id: uuid.UUID, replies: list[AgentMessage]) -> None:
    """Add the replies to a conversation's transcript."""
    async with SessionFactory() as session:
        await add_messages(session, conversation_id, replies)
        await session.commit()


async def record_replies(agent: LangGraphAgent, run_input: RunAgentInput) -> None:
    """Add the assistant's answers to a run's message to the conversation's transcript."""
    conversation_id = uuid.UUID(run_input.thread_id)
    history = await chat_client.read_history(agent, conversation_id)
    replies = replies_after(history, run_input.messages[0].id)
    await save_replies(conversation_id, replies)
