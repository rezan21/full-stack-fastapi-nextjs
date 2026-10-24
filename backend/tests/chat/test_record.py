from functools import partial

import pytest
from ag_ui.core import RunAgentInput
from langgraph.checkpoint.memory import InMemorySaver
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import browser as agent_browser
from src.agent import factory as agent_factory
from src.agent import streaming as agent_streaming
from src.agent.schemas import AgentMessage
from src.chat import service as chat_service
from src.chat.models import Conversation
from tests.utils.agent import (
    CONTEXT,
    PartialModel,
    browser_answer_input,
    collect,
    flying_to_london,
    replying,
    run_input,
    stop_midway,
)
from tests.utils.chat import agent_asking_to_delete, answer_input
from tests.utils.user import create_random_user


@pytest.fixture
async def conversation(db: AsyncSession) -> Conversation:
    created = Conversation(owner_id=(await create_random_user(db)).id)
    db.add(created)
    await db.commit()
    return created


async def record_message(
    db: AsyncSession, conversation: Conversation, run: RunAgentInput, text: str
) -> None:
    await chat_service.add_messages(
        db, conversation.id, [AgentMessage(run.messages[0].id, "user", text)]
    )
    await db.commit()


async def test_the_answers_of_a_run_are_recorded_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent = agent_factory.build_agent(
        replying("First answer.", "Second answer."), InMemorySaver()
    )
    for text in ("one", "two"):
        run = run_input(text, str(conversation.id))
        await record_message(db, conversation, run, text)
        await collect(agent_streaming.stream_events(agent, run, CONTEXT))
        await chat_service.record_replies(agent, run)

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
    agent = agent_factory.build_agent(replying("Only once."), InMemorySaver())
    run = run_input("hello", str(conversation.id))
    await collect(agent_streaming.stream_events(agent, run, CONTEXT))

    await chat_service.record_replies(agent, run)
    await chat_service.record_replies(agent, run)

    messages, _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [m.content for m in messages] == ["Only once."]


async def test_the_answer_after_a_browser_tool_is_recorded_once(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent = agent_factory.build_agent(
        flying_to_london("Now showing London."), InMemorySaver()
    )
    tools = agent_browser.offered(["fly_to"])
    first = run_input("go", str(conversation.id), tools=tools)
    await record_message(db, conversation, first, "go")
    await collect(agent_streaming.stream_events(agent, first, CONTEXT))
    await chat_service.record_replies(agent, first)
    answer = browser_answer_input(
        "The map now shows London.", tools, thread_id=str(conversation.id)
    )
    await collect(agent_streaming.stream_events(agent, answer, CONTEXT))

    await chat_service.record_replies(agent, answer)
    await chat_service.record_replies(agent, answer)

    messages, _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [(m.role, m.content) for m in messages] == [
        ("user", "go"),
        ("assistant", "Now showing London."),
    ]


async def test_a_reply_cut_off_midway_is_recorded_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    model = PartialModel(chunks=["Once upon ", "a time"])
    agent = agent_factory.build_agent(model, InMemorySaver())
    run = run_input("tell me a story", str(conversation.id))
    await record_message(db, conversation, run, "tell me a story")

    await stop_midway(
        agent,
        run,
        len(model.chunks),
        partial(chat_service.record_replies, agent, run),
    )

    messages, _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [(m.role, m.content) for m in messages] == [
        ("user", "tell me a story"),
        ("assistant", "Once upon a time"),
    ]


def agent_said(agent_id: str, role: str, content: str) -> AgentMessage:
    return AgentMessage(id=agent_id, role=role, content=content)  # type: ignore[arg-type]


def test_the_replies_are_what_the_assistant_said_after_the_message_it_answers() -> None:
    history = [
        agent_said("u-1", "user", "an old question"),
        agent_said("a-1", "assistant", "an old answer"),
        agent_said("u-2", "user", "the new question"),
        agent_said("a-2", "assistant", "I will look"),
        agent_said("a-3", "assistant", "the final answer"),
    ]

    replies = chat_service.replies_after(history, "u-2")

    assert [reply.id for reply in replies] == ["a-2", "a-3"]


def test_a_message_that_is_not_in_the_history_has_no_replies() -> None:
    history = [agent_said("u-1", "user", "hi"), agent_said("a-1", "assistant", "hello")]

    assert chat_service.replies_after(history, "missing") == []


async def test_the_reply_after_the_users_answer_is_recorded_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (request_id,), _ = await agent_asking_to_delete(db, conversation)
    run = await chat_service.start_run(
        db, conversation, answer_input((request_id, True)), agent
    )

    await collect(agent_streaming.stream_events(agent, run, CONTEXT))
    await chat_service.record_replies(agent, run)

    messages, _ = await chat_service.read_messages(db, conversation.id, limit=10)
    assert [(m.role, m.content) for m in messages] == [("assistant", "Left it.")]
