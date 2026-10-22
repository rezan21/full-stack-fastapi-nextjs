import pytest
from ag_ui.core import RunAgentInput
from langgraph.checkpoint.memory import InMemorySaver
from sqlmodel.ext.asyncio.session import AsyncSession

from src.chat import client as chat_client
from src.chat import service as chat_service
from src.chat.models import Conversation
from src.chat.schemas import AgentMessage
from tests.utils.chat import collect, replying
from tests.utils.user import create_random_user


@pytest.fixture
async def conversation(db: AsyncSession) -> Conversation:
    created = Conversation(owner_id=(await create_random_user(db)).id)
    db.add(created)
    await db.commit()
    return created


def run_for(conversation: Conversation, text: str) -> RunAgentInput:
    from tests.utils.chat import client_input

    return chat_service.build_run_input(
        client_input(messages=[{"id": "m1", "role": "user", "content": text}]),
        conversation.id,
    )


async def test_the_answers_of_a_run_are_recorded_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent = chat_client.build_agent(
        replying("First answer.", "Second answer."), InMemorySaver()
    )
    for text in ("one", "two"):
        run_input = run_for(conversation, text)
        await chat_service.add_messages(
            db,
            conversation.id,
            [AgentMessage(run_input.messages[0].id, "user", text)],
        )
        await db.commit()
        await collect(chat_client.stream_events(agent, run_input))
        await chat_service.record_replies(agent, run_input)

    messages, count = await chat_service.read_messages(db, conversation.id, limit=10)

    assert [(m.role, m.content) for m in messages] == [
        ("user", "one"),
        ("assistant", "First answer."),
        ("user", "two"),
        ("assistant", "Second answer."),
    ]
    assert count == 4


async def test_recording_the_same_run_twice_does_not_repeat_the_answer(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent = chat_client.build_agent(replying("Only once."), InMemorySaver())
    run_input = run_for(conversation, "hello")
    await collect(chat_client.stream_events(agent, run_input))

    await chat_service.record_replies(agent, run_input)
    await chat_service.record_replies(agent, run_input)

    messages, _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [m.content for m in messages] == ["Only once."]
