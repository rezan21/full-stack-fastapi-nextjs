from ag_ui.core import (
    BaseEvent,
    EventType,
    ResumeEntry,
    TextMessageContentEvent,
    ToolCallResultEvent,
)
from ag_ui_langgraph import LangGraphAgent
from langchain_core.messages import ToolMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import interrupts as agent_interrupts
from src.agent import threads as agent_threads
from src.users.models import User
from tests.utils.agent import (
    THREAD,
    agent_for,
    answer,
    ask_to_delete,
    deleting,
    interrupts_of,
    replying,
    resume_input,
    run_as,
    run_input,
    tool_results,
)
from tests.utils.item import add_items, stored
from tests.utils.user import create_random_user


async def answer_all(
    owner: User, agent: LangGraphAgent, *answers: ResumeEntry
) -> list[BaseEvent]:
    return await run_as(owner, agent, resume_input(list(answers)))


async def test_an_interrupt_is_open_until_the_user_answers_it(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)

    agent, events = await ask_to_delete(owner, deleting(item))

    (interrupt,) = interrupts_of(events)
    assert interrupt.reason == "tool_call"
    assert interrupt.tool_call_id == "call-0"
    assert await stored(item.id)
    assert not tool_results(events)
    assert [
        r.interrupt_id for r in await agent_threads.open_interrupts(agent, THREAD)
    ] == [interrupt.id]


async def test_the_old_interrupt_event_is_not_sent_to_the_browser(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)

    _, events = await ask_to_delete(owner, deleting(item))

    assert [e for e in events if e.type == EventType.CUSTOM] == []


async def test_several_interrupts_are_asked_together_and_answered_one_by_one(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    first, second = await add_items(db, owner, 2)
    agent, events = await ask_to_delete(owner, deleting(first, second))
    interrupts = {i.tool_call_id: i for i in interrupts_of(events)}

    await answer_all(
        owner,
        agent,
        answer(interrupts["call-0"], True),
        answer(interrupts["call-1"], False),
    )

    assert await stored(first.id) is None
    assert await stored(second.id)


async def test_a_new_message_closes_the_open_interrupt_and_the_model_is_told(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    model = deleting(item, texts=("Alright, I left it.",))
    agent, _ = await ask_to_delete(owner, model)

    await agent_threads.cancel_pending_calls(agent, THREAD)
    events = await run_as(owner, agent, run_input("never mind"))

    assert await agent_threads.open_interrupts(agent, THREAD) == []
    assert await stored(item.id)
    said = "".join(e.delta for e in events if isinstance(e, TextMessageContentEvent))
    assert said == "Alright, I left it."
    told = [m for m in model.seen[-1] if isinstance(m, ToolMessage)]
    assert [m.content for m in told] == [agent_interrupts.UNANSWERED_RESULT]


async def test_closing_calls_with_none_pending_changes_nothing() -> None:
    agent = agent_for(replying())

    await agent_threads.cancel_pending_calls(agent, THREAD)

    assert await agent_threads.open_interrupts(agent, THREAD) == []


async def test_the_agent_keeps_asking_through_a_copy_made_for_each_run() -> None:
    copy = agent_for(replying()).clone()

    assert copy.emit_interrupt_outcome is True
    assert copy.enable_legacy_on_interrupt_event is False


async def test_the_resumed_run_reports_the_result_without_announcing_the_call_again(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent, events = await ask_to_delete(owner, deleting(item))
    (interrupt,) = interrupts_of(events)

    resumed = await answer_all(owner, agent, answer(interrupt, True))

    assert not [e for e in resumed if e.type == EventType.TOOL_CALL_START]
    assert [e.tool_call_id for e in resumed if isinstance(e, ToolCallResultEvent)] == [
        "call-0"
    ]
