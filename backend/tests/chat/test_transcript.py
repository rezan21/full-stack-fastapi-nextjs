import uuid

import pytest
from sqlmodel import col, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.chat import service as chat_service
from src.chat.models import ChatMessage, Conversation
from src.chat.schemas import AgentMessage
from tests.utils.user import create_random_user


@pytest.fixture
async def conversation(db: AsyncSession) -> Conversation:
    owner = await create_random_user(db)
    created = Conversation(owner_id=owner.id)
    db.add(created)
    await db.commit()
    return created


def said(role: str, content: str, agent_id: str | None = None) -> AgentMessage:
    return AgentMessage(id=agent_id or str(uuid.uuid4()), role=role, content=content)  # type: ignore[arg-type]


async def test_messages_are_read_back_in_the_order_they_were_added(
    db: AsyncSession, conversation: Conversation
) -> None:
    await chat_service.add_messages(
        db,
        conversation.id,
        [said("user", "one"), said("assistant", "two"), said("assistant", "three")],
    )
    await db.commit()

    messages, count = await chat_service.read_messages(db, conversation.id, limit=10)

    assert [(m.role, m.content) for m in messages] == [
        ("user", "one"),
        ("assistant", "two"),
        ("assistant", "three"),
    ]
    assert count == 3
    seqs = [m.seq for m in messages]
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 3


async def test_a_message_keeps_the_id_the_agent_gave_it_when_that_is_a_uuid(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent_id = str(uuid.uuid4())

    await chat_service.add_messages(db, conversation.id, [said("user", "hi", agent_id)])
    await db.commit()

    (message,), _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert message.id == uuid.UUID(agent_id)
    assert message.agent_message_id == agent_id


async def test_a_message_the_agent_named_another_way_still_gets_a_uuid(
    db: AsyncSession, conversation: Conversation
) -> None:
    await chat_service.add_messages(
        db, conversation.id, [said("assistant", "hello", "lc_run--019abc-0")]
    )
    await db.commit()

    (message,), _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert isinstance(message.id, uuid.UUID)
    assert message.agent_message_id == "lc_run--019abc-0"


async def test_adding_the_same_message_again_changes_nothing(
    db: AsyncSession, conversation: Conversation
) -> None:
    reply = said("assistant", "an answer", "lc_run--1")
    await chat_service.add_messages(db, conversation.id, [reply])
    await db.commit()

    await chat_service.add_messages(
        db, conversation.id, [reply, said("assistant", "more", "lc_run--2")]
    )
    await db.commit()

    messages, count = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [m.content for m in messages] == ["an answer", "more"]
    assert count == 2


async def test_two_conversations_can_hold_the_same_agent_message_id(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    first, second = Conversation(owner_id=owner.id), Conversation(owner_id=owner.id)
    db.add_all([first, second])
    await db.commit()

    for conversation in (first, second):
        await chat_service.add_messages(
            db, conversation.id, [said("user", "hi", "same-id")]
        )
    await db.commit()

    assert (await chat_service.read_messages(db, first.id, limit=10))[1] == 1
    assert (await chat_service.read_messages(db, second.id, limit=10))[1] == 1


async def test_only_the_latest_messages_are_read_but_the_count_is_the_whole_conversation(
    db: AsyncSession, conversation: Conversation
) -> None:
    await chat_service.add_messages(
        db, conversation.id, [said("user", f"message {n}") for n in range(5)]
    )
    await db.commit()

    messages, count = await chat_service.read_messages(db, conversation.id, limit=2)

    assert [m.content for m in messages] == ["message 3", "message 4"]
    assert count == 5


async def test_a_conversation_with_no_messages_reads_as_empty(
    db: AsyncSession, conversation: Conversation
) -> None:
    assert await chat_service.read_messages(db, conversation.id, limit=10) == ([], 0)


async def test_messages_go_with_their_conversation(
    db: AsyncSession, conversation: Conversation
) -> None:
    await chat_service.add_messages(db, conversation.id, [said("user", "hi")])
    await db.commit()
    conversation_id = conversation.id

    await db.exec(delete(Conversation).where(col(Conversation.id) == conversation_id))
    await db.commit()

    assert (
        await db.exec(
            select(ChatMessage).where(
                col(ChatMessage.conversation_id) == conversation_id
            )
        )
    ).all() == []
