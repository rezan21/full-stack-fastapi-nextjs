import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, func, select

from app.models import ChatMessage


@dataclass(frozen=True)
class AgentMessage:
    id: str
    role: Literal["user", "assistant"]
    content: str


def message_id(agent_message_id: str) -> uuid.UUID:
    """Return the agent's message id as a UUID when it is one, or a new UUID."""
    try:
        return uuid.UUID(agent_message_id)
    except ValueError:
        return uuid.uuid4()


def add_messages(
    session: Session, conversation_id: uuid.UUID, messages: Iterable[AgentMessage]
) -> None:
    """Add messages to a conversation's transcript, skipping any it already holds."""
    for message in messages:
        session.exec(
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


def read_messages(
    session: Session, conversation_id: uuid.UUID, limit: int
) -> tuple[list[ChatMessage], int]:
    """Return the latest messages of a conversation in order, and how many it holds."""
    in_conversation = col(ChatMessage.conversation_id) == conversation_id
    count = session.exec(
        select(func.count()).select_from(ChatMessage).where(in_conversation)
    ).one()
    latest = session.exec(
        select(ChatMessage)
        .where(in_conversation)
        .order_by(col(ChatMessage.seq).desc())
        .limit(limit)
    ).all()
    return list(reversed(latest)), count
