import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, StringConstraints
from pydantic import Field as PydanticField
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy import BigInteger, Column, Identity, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

PASSWORD_MAX_LENGTH = 128
CONVERSATION_TITLE_MAX_LENGTH = 60
MAX_MESSAGE_CHARS = 4000
EMAIL_PATTERN = (
    r"^[A-Za-z0-9_'+-]+(\.[A-Za-z0-9_'+-]+)*"
    r"@([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

Email = Annotated[
    str,
    Field(max_length=255),
    StringConstraints(pattern=EMAIL_PATTERN),
    AfterValidator(str.lower),
]
FullName = Annotated[str, Field(min_length=1, max_length=255)]
Password = Annotated[str, Field(min_length=8, max_length=PASSWORD_MAX_LENGTH)]
CurrentPassword = Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]
ItemTitle = Annotated[str, Field(min_length=1, max_length=255)]
ItemDescription = Annotated[str | None, Field(max_length=255)]


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class UserBase(SQLModel):
    email: Email = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: FullName


class UserCreate(UserBase):
    password: Password


class Credentials(SQLModel):
    username: Email
    password: CurrentPassword


class UserRegister(SQLModel):
    email: Email
    full_name: FullName


class UserUpdateMe(SQLModel):
    full_name: FullName | MISSING = MISSING  # type: ignore[valid-type]


class EmailChange(SQLModel):
    email: Email
    current_password: CurrentPassword


class AccountDeletion(SQLModel):
    current_password: CurrentPassword


class EmailChangeConfirm(SQLModel):
    token: str


class UpdatePassword(SQLModel):
    current_password: CurrentPassword
    new_password: Password


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    token_version: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    created_at: datetime = Field(default_factory=get_datetime_utc)
    items: list[Item] = Relationship(back_populates="owner", cascade_delete=True)
    conversations: list[Conversation] = Relationship(
        back_populates="owner", cascade_delete=True
    )


class AuthThrottle(SQLModel, table=True):
    __tablename__ = "auth_throttle"

    key: str = Field(primary_key=True, max_length=64)
    failures: int = 0
    last_failure_at: datetime = Field(default_factory=get_datetime_utc, index=True)
    locked_until: datetime | None = None


class UserPublic(SQLModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime


class ItemBase(SQLModel):
    title: ItemTitle
    description: ItemDescription = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    title: ItemTitle | MISSING = MISSING  # type: ignore[valid-type]
    description: ItemDescription | MISSING = MISSING  # type: ignore[valid-type]


class Item(ItemBase, table=True):
    __table_args__ = (Index("ix_item_owner_id_created_at", "owner_id", "created_at"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=get_datetime_utc)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(SQLModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    created_at: datetime


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


class Conversation(SQLModel, table=True):
    __table_args__ = (
        Index("ix_conversation_owner_id_updated_at", "owner_id", "updated_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    title: str | None = Field(default=None, max_length=CONVERSATION_TITLE_MAX_LENGTH)
    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)
    owner: User | None = Relationship(back_populates="conversations")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    __table_args__ = (
        UniqueConstraint("conversation_id", "agent_message_id"),
        Index("ix_chat_message_conversation_id_seq", "conversation_id", "seq"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    seq: int | None = Field(
        default=None, sa_column=Column(BigInteger, Identity(), nullable=False)
    )
    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id", nullable=False, ondelete="CASCADE"
    )
    agent_message_id: str = Field(max_length=255)
    role: str = Field(max_length=9)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=get_datetime_utc)


class ChatUsage(SQLModel, table=True):
    __tablename__ = "chat_usage"

    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    window_start: datetime = Field(primary_key=True)
    runs: int = 0


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


class Message(SQLModel):
    message: str


class HTTPError(SQLModel):
    detail: str


class Token(SQLModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenPayload(SQLModel):
    sub: str | None = None
    ver: int | None = None


class PasswordRecovery(SQLModel):
    email: Email


class NewPassword(SQLModel):
    token: str
    new_password: Password
