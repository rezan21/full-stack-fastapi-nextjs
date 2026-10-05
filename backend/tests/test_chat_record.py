import asyncio

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from sqlmodel import Session

from app.core import chat, transcript
from app.models import Conversation
from tests.utils.chat import collect, replying
from tests.utils.user import create_random_user


@pytest.fixture
def conversation(db: Session) -> Conversation:
    created = Conversation(owner_id=create_random_user(db).id)
    db.add(created)
    db.commit()
    return created


def run_for(conversation: Conversation, text: str) -> chat.RunAgentInput:
    from tests.utils.chat import client_input

    return chat.build_run_input(
        client_input(messages=[{"id": "m1", "role": "user", "content": text}]),
        conversation.id,
    )


def test_the_answers_of_a_run_are_recorded_in_the_transcript(
    db: Session, conversation: Conversation
) -> None:
    agent = chat.build_agent(
        replying("First answer.", "Second answer."), InMemorySaver()
    )
    for text in ("one", "two"):
        run_input = run_for(conversation, text)
        transcript.add_messages(
            db,
            conversation.id,
            [transcript.AgentMessage(run_input.messages[0].id, "user", text)],
        )
        db.commit()
        collect(chat.stream_events(agent, run_input))
        asyncio.run(chat.record_replies(agent, run_input))

    messages, count = transcript.read_messages(db, conversation.id, limit=10)

    assert [(m.role, m.content) for m in messages] == [
        ("user", "one"),
        ("assistant", "First answer."),
        ("user", "two"),
        ("assistant", "Second answer."),
    ]
    assert count == 4


def test_recording_the_same_run_twice_does_not_repeat_the_answer(
    db: Session, conversation: Conversation
) -> None:
    agent = chat.build_agent(replying("Only once."), InMemorySaver())
    run_input = run_for(conversation, "hello")
    collect(chat.stream_events(agent, run_input))

    asyncio.run(chat.record_replies(agent, run_input))
    asyncio.run(chat.record_replies(agent, run_input))

    messages, _ = transcript.read_messages(db, conversation.id, limit=10)
    assert [m.content for m in messages] == ["Only once."]
