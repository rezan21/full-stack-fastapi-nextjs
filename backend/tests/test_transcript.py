import uuid

import pytest
from sqlmodel import Session, col, delete, select

from app.core import transcript
from app.core.transcript import AgentMessage
from app.models import ChatMessage, Conversation
from tests.utils.user import create_random_user


@pytest.fixture
def conversation(db: Session) -> Conversation:
    owner = create_random_user(db)
    created = Conversation(owner_id=owner.id)
    db.add(created)
    db.commit()
    return created


def said(role: str, content: str, agent_id: str | None = None) -> AgentMessage:
    return AgentMessage(id=agent_id or str(uuid.uuid4()), role=role, content=content)  # type: ignore[arg-type]


def test_messages_are_read_back_in_the_order_they_were_added(
    db: Session, conversation: Conversation
) -> None:
    transcript.add_messages(
        db,
        conversation.id,
        [said("user", "one"), said("assistant", "two"), said("assistant", "three")],
    )
    db.commit()

    messages, count = transcript.read_messages(db, conversation.id, limit=10)

    assert [(m.role, m.content) for m in messages] == [
        ("user", "one"),
        ("assistant", "two"),
        ("assistant", "three"),
    ]
    assert count == 3
    seqs = [m.seq for m in messages]
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 3


def test_a_message_keeps_the_id_the_agent_gave_it_when_that_is_a_uuid(
    db: Session, conversation: Conversation
) -> None:
    agent_id = str(uuid.uuid4())

    transcript.add_messages(db, conversation.id, [said("user", "hi", agent_id)])
    db.commit()

    (message,), _ = transcript.read_messages(db, conversation.id, limit=10)
    assert message.id == uuid.UUID(agent_id)
    assert message.agent_message_id == agent_id


def test_a_message_the_agent_named_another_way_still_gets_a_uuid(
    db: Session, conversation: Conversation
) -> None:
    transcript.add_messages(
        db, conversation.id, [said("assistant", "hello", "lc_run--019abc-0")]
    )
    db.commit()

    (message,), _ = transcript.read_messages(db, conversation.id, limit=10)
    assert isinstance(message.id, uuid.UUID)
    assert message.agent_message_id == "lc_run--019abc-0"


def test_adding_the_same_message_again_changes_nothing(
    db: Session, conversation: Conversation
) -> None:
    reply = said("assistant", "an answer", "lc_run--1")
    transcript.add_messages(db, conversation.id, [reply])
    db.commit()

    transcript.add_messages(
        db, conversation.id, [reply, said("assistant", "more", "lc_run--2")]
    )
    db.commit()

    messages, count = transcript.read_messages(db, conversation.id, limit=10)
    assert [m.content for m in messages] == ["an answer", "more"]
    assert count == 2


def test_two_conversations_can_hold_the_same_agent_message_id(db: Session) -> None:
    owner = create_random_user(db)
    first, second = Conversation(owner_id=owner.id), Conversation(owner_id=owner.id)
    db.add_all([first, second])
    db.commit()

    for conversation in (first, second):
        transcript.add_messages(db, conversation.id, [said("user", "hi", "same-id")])
    db.commit()

    assert transcript.read_messages(db, first.id, limit=10)[1] == 1
    assert transcript.read_messages(db, second.id, limit=10)[1] == 1


def test_only_the_latest_messages_are_read_but_the_count_is_the_whole_conversation(
    db: Session, conversation: Conversation
) -> None:
    transcript.add_messages(
        db, conversation.id, [said("user", f"message {n}") for n in range(5)]
    )
    db.commit()

    messages, count = transcript.read_messages(db, conversation.id, limit=2)

    assert [m.content for m in messages] == ["message 3", "message 4"]
    assert count == 5


def test_a_conversation_with_no_messages_reads_as_empty(
    db: Session, conversation: Conversation
) -> None:
    assert transcript.read_messages(db, conversation.id, limit=10) == ([], 0)


def test_messages_go_with_their_conversation(
    db: Session, conversation: Conversation
) -> None:
    transcript.add_messages(db, conversation.id, [said("user", "hi")])
    db.commit()
    conversation_id = conversation.id

    db.exec(delete(Conversation).where(col(Conversation.id) == conversation_id))
    db.commit()

    assert (
        db.exec(
            select(ChatMessage).where(
                col(ChatMessage.conversation_id) == conversation_id
            )
        ).all()
        == []
    )
