import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, Identity, Index, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.models import get_datetime_utc

CONVERSATION_TITLE_MAX_LENGTH = 60


class Conversation(SQLModel, table=True):
    __tablename__ = "chat_conversation"
    __table_args__ = (
        Index("chat_conversation_owner_id_updated_at_idx", "owner_id", "updated_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    title: str | None = Field(default=None, max_length=CONVERSATION_TITLE_MAX_LENGTH)
    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    __table_args__ = (
        UniqueConstraint("conversation_id", "agent_message_id"),
        Index("chat_message_conversation_id_seq_idx", "conversation_id", "seq"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    seq: int | None = Field(
        default=None, sa_column=Column(BigInteger, Identity(), nullable=False)
    )
    conversation_id: uuid.UUID = Field(
        foreign_key="chat_conversation.id", nullable=False, ondelete="CASCADE"
    )
    agent_message_id: str = Field(max_length=255)
    role: str = Field(max_length=9)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=get_datetime_utc)


class ChatUsage(SQLModel, table=True):
    __tablename__ = "chat_usage"

    owner_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    window_started_at: datetime = Field(primary_key=True)
    runs: int = 0
