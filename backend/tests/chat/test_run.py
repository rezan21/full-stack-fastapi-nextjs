from typing import Any

import pytest
from ag_ui.core import ToolMessage
from ag_ui_langgraph import LangGraphAgent
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import browser as agent_browser
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from src.chat import service as chat_service
from src.chat.exceptions import (
    AnswerWithMessage,
    InvalidChatInput,
    InvalidToolResult,
    NoOpenInterrupt,
    NoPendingToolCall,
)
from src.chat.models import ChatUsage, Conversation
from src.chat.schemas import MAX_MESSAGE_CHARS, MAX_TOOL_RESULT_CHARS
from tests.utils.agent import (
    CONTEXT,
    agent_for,
    collect,
    flying_to_london,
    replying,
    run_input,
)
from tests.utils.chat import (
    agent_asking_to_delete,
    answer_input,
    client_input,
    tool_result_input,
)
from tests.utils.user import create_random_user


@pytest.fixture
async def conversation(db: AsyncSession) -> Conversation:
    created = Conversation(owner_id=(await create_random_user(db)).id)
    db.add(created)
    await db.commit()
    return created


@pytest.fixture
def agent() -> LangGraphAgent:
    return agent_for(replying())


async def agent_waiting_on_the_browser(conversation: Conversation) -> LangGraphAgent:
    waiting = agent_for(flying_to_london("Now showing London."))
    tools = agent_browser.offered(["fly_to"])
    first = run_input("go", str(conversation.id), tools=tools, run_id="r1")
    await collect(agent_streaming.stream_events(waiting, first, CONTEXT))
    return waiting


def one_message(text: str) -> Any:
    return client_input(messages=[{"id": "m1", "role": "user", "content": text}])


def test_the_text_of_a_run_is_the_newest_user_message() -> None:
    assert chat_service.newest_user_text(client_input()) == "newest question"


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"id": "a", "role": "assistant", "content": "only the assistant"}],
        [{"id": "a", "role": "user", "content": ""}],
        [{"id": "a", "role": "user", "content": "   \n\t"}],
        [
            {
                "id": "a",
                "role": "user",
                "content": [{"type": "text", "text": "not a plain string"}],
            }
        ],
    ],
)
def test_input_without_a_plain_text_user_message_is_refused(
    messages: list[dict[str, Any]],
) -> None:
    with pytest.raises(InvalidChatInput):
        chat_service.newest_user_text(client_input(messages=messages))


def test_a_message_at_the_length_limit_is_accepted_and_one_over_is_not() -> None:
    at_limit = "x" * MAX_MESSAGE_CHARS

    assert chat_service.newest_user_text(one_message(at_limit)) == at_limit
    with pytest.raises(InvalidChatInput):
        chat_service.newest_user_text(one_message(at_limit + "x"))


async def test_a_run_belongs_to_the_conversation_and_not_the_thread_the_client_names(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    run_input = await chat_service.start_run(db, conversation, client_input(), agent)

    assert run_input.thread_id == str(conversation.id)


async def test_a_run_answers_only_the_newest_user_message(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    run_input = await chat_service.start_run(db, conversation, client_input(), agent)

    assert [(m.role, m.content) for m in run_input.messages] == [
        ("user", "newest question")
    ]


async def test_everything_the_client_could_steer_the_run_with_is_dropped(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    body = client_input(resume=[{"interruptId": "i-1", "status": "cancelled"}])
    run_input = await chat_service.start_run(db, conversation, body, agent)

    assert not run_input.state
    assert not run_input.tools
    assert not run_input.context
    assert not run_input.forwarded_props
    assert not run_input.resume


async def test_a_browser_tool_the_server_defines_is_offered_and_others_are_not(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    body = client_input(tools=[{"name": "fly_to"}, {"name": "steal"}])

    run_input = await chat_service.start_run(db, conversation, body, agent)

    assert [tool.name for tool in run_input.tools or []] == ["fly_to"]


async def test_a_browser_tools_answer_becomes_the_runs_only_message(
    db: AsyncSession, conversation: Conversation
) -> None:
    waiting = await agent_waiting_on_the_browser(conversation)
    body = tool_result_input(tools=[{"name": "fly_to"}])

    run_input = await chat_service.start_run(db, conversation, body, waiting)

    (message,) = run_input.messages
    assert isinstance(message, ToolMessage)
    assert message.content == "The map now shows London."
    assert message.tool_call_id == "call-1"
    assert [tool.name for tool in run_input.tools or []] == ["fly_to"]


async def test_a_browser_tools_answer_is_not_a_message_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    waiting = await agent_waiting_on_the_browser(conversation)

    await chat_service.start_run(db, conversation, tool_result_input(), waiting)

    messages, count = await chat_service.read_messages(db, conversation.id, limit=10)
    assert (list(messages), count) == ([], 0)


async def test_a_browser_tools_answer_counts_as_a_run(
    db: AsyncSession, conversation: Conversation
) -> None:
    waiting = await agent_waiting_on_the_browser(conversation)

    await chat_service.start_run(db, conversation, tool_result_input(), waiting)

    usage = (
        await db.exec(
            select(ChatUsage).where(ChatUsage.owner_id == conversation.owner_id)
        )
    ).one()
    assert usage.runs == 1


async def test_an_answer_to_a_call_nobody_made_is_refused(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    with pytest.raises(NoPendingToolCall):
        await chat_service.start_run(db, conversation, tool_result_input(), agent)


async def test_a_call_can_only_be_answered_once(
    db: AsyncSession, conversation: Conversation
) -> None:
    waiting = await agent_waiting_on_the_browser(conversation)
    answered = await chat_service.start_run(
        db, conversation, tool_result_input(), waiting
    )
    await collect(agent_streaming.stream_events(waiting, answered, CONTEXT))

    with pytest.raises(NoPendingToolCall):
        await chat_service.start_run(db, conversation, tool_result_input(), waiting)


@pytest.mark.parametrize(
    "content", [None, 7, ["not text"], "x" * (MAX_TOOL_RESULT_CHARS + 1)]
)
async def test_an_answer_that_is_not_short_text_is_refused(
    db: AsyncSession, conversation: Conversation, content: Any
) -> None:
    waiting = await agent_waiting_on_the_browser(conversation)

    with pytest.raises(InvalidToolResult):
        await chat_service.start_run(
            db, conversation, tool_result_input(content), waiting
        )


async def test_the_users_answer_becomes_the_runs_only_input(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)

    run_input = await chat_service.start_run(
        db, conversation, answer_input((interrupt_id, True)), agent
    )

    assert run_input.messages == []
    (entry,) = run_input.resume or []
    assert (entry.interrupt_id, entry.status) == (interrupt_id, "resolved")
    assert entry.payload == {"approved": True}


async def test_an_answer_is_not_a_message_in_the_transcript(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)

    await chat_service.start_run(
        db, conversation, answer_input((interrupt_id, True)), agent
    )

    messages, count = await chat_service.read_messages(db, conversation.id, limit=10)
    assert (list(messages), count) == ([], 0)


async def test_an_answer_counts_as_a_run(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)

    await chat_service.start_run(
        db, conversation, answer_input((interrupt_id, False)), agent
    )

    usage = (
        await db.exec(
            select(ChatUsage).where(ChatUsage.owner_id == conversation.owner_id)
        )
    ).one()
    assert usage.runs == 1


async def test_an_answer_to_an_interrupt_nobody_opened_is_refused(
    db: AsyncSession, conversation: Conversation, agent: LangGraphAgent
) -> None:
    with pytest.raises(NoOpenInterrupt):
        await chat_service.start_run(
            db, conversation, answer_input(("made-up", True)), agent
        )


async def test_an_answer_to_another_interrupt_is_refused(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, _, _ = await agent_asking_to_delete(db, conversation)

    with pytest.raises(NoOpenInterrupt):
        await chat_service.start_run(
            db, conversation, answer_input(("made-up", True)), agent
        )


async def test_every_open_interrupt_has_to_be_answered_together(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (first, _), _ = await agent_asking_to_delete(db, conversation, count=2)

    with pytest.raises(NoOpenInterrupt):
        await chat_service.start_run(
            db, conversation, answer_input((first, True)), agent
        )


async def test_an_interrupt_can_only_be_answered_once(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)
    answered = await chat_service.start_run(
        db, conversation, answer_input((interrupt_id, True)), agent
    )
    await collect(agent_streaming.stream_events(agent, answered, CONTEXT))

    with pytest.raises(NoOpenInterrupt):
        await chat_service.start_run(
            db, conversation, answer_input((interrupt_id, True)), agent
        )


async def test_an_answer_sent_with_the_whole_transcript_is_still_an_answer(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)
    transcript = [
        {"id": "m1", "role": "user", "content": "delete it"},
        {"id": "m2", "role": "assistant", "content": "Asking."},
    ]
    body = answer_input((interrupt_id, True), messages=transcript)

    run_input = await chat_service.start_run(db, conversation, body, agent)

    assert run_input.messages == []
    assert run_input.resume


async def test_a_new_message_closes_the_interrupt_the_user_left_open(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, _, items = await agent_asking_to_delete(db, conversation)

    run_input = await chat_service.start_run(
        db, conversation, one_message("never mind"), agent
    )

    assert [(m.role, m.content) for m in run_input.messages] == [("user", "never mind")]
    assert await agent_threads.open_interrupts(agent, str(conversation.id)) == []


async def test_a_message_sent_with_the_interrupts_cancelled_is_a_message(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)
    body = answer_input(
        (interrupt_id, None),
        messages=[{"id": "m3", "role": "user", "content": "never mind"}],
    )

    run_input = await chat_service.start_run(db, conversation, body, agent)

    assert [(m.role, m.content) for m in run_input.messages] == [("user", "never mind")]
    assert not run_input.resume
    assert await agent_threads.open_interrupts(agent, str(conversation.id)) == []


async def test_an_approval_sent_with_a_new_message_is_refused_and_stays_open(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)
    body = answer_input(
        (interrupt_id, True),
        messages=[{"id": "m3", "role": "user", "content": "never mind"}],
    )

    with pytest.raises(AnswerWithMessage):
        await chat_service.start_run(db, conversation, body, agent)

    open_ids = [
        interrupt.interrupt_id
        for interrupt in await agent_threads.open_interrupts(
            agent, str(conversation.id)
        )
    ]
    assert open_ids == [interrupt_id]


async def test_an_approval_mixed_with_cancellations_and_a_new_message_is_refused_whole(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (first, second), _ = await agent_asking_to_delete(db, conversation, count=2)
    body = answer_input(
        (first, True),
        (second, None),
        messages=[{"id": "m3", "role": "user", "content": "never mind"}],
    )

    with pytest.raises(AnswerWithMessage):
        await chat_service.start_run(db, conversation, body, agent)

    open_ids = sorted(
        interrupt.interrupt_id
        for interrupt in await agent_threads.open_interrupts(
            agent, str(conversation.id)
        )
    )
    assert open_ids == sorted([first, second])


async def test_a_browser_tools_answer_sent_with_an_answer_is_refused_and_the_interrupt_stays_open(
    db: AsyncSession, conversation: Conversation
) -> None:
    agent, (interrupt_id,), _ = await agent_asking_to_delete(db, conversation)
    body = answer_input(
        (interrupt_id, True),
        messages=[
            {
                "id": "m9",
                "role": "tool",
                "toolCallId": "call-1",
                "content": "The map now shows London.",
            }
        ],
    )

    with pytest.raises(AnswerWithMessage):
        await chat_service.start_run(db, conversation, body, agent)

    open_ids = [
        interrupt.interrupt_id
        for interrupt in await agent_threads.open_interrupts(
            agent, str(conversation.id)
        )
    ]
    assert open_ids == [interrupt_id]
