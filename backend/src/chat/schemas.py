import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel

MAX_MESSAGE_CHARS = 4000


@dataclass(frozen=True)
class AgentMessage:
    id: str
    role: Literal["user", "assistant"]
    content: str


class ConversationPublic(SQLModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationsPublic(SQLModel):
    data: list[ConversationPublic]
    count: int


class ChatRunMessage(SQLModel):
    role: str
    content: Any = None


ChatRunMessages = Annotated[
    list[ChatRunMessage],
    PydanticField(json_schema_extra={"x-max-user-message-length": MAX_MESSAGE_CHARS}),
]


class ChatRun(SQLModel):
    thread_id: str = Field(alias="threadId")
    run_id: str = Field(alias="runId")
    messages: ChatRunMessages


class ChatMessagePublic(SQLModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatMessagesPublic(SQLModel):
    data: list[ChatMessagePublic]
    count: int
