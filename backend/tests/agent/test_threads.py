import uuid

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.agent import factory as agent_factory
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from tests.utils.agent import (
    CONTEXT,
    OTHER_THREAD,
    THREAD,
    ScriptedModel,
    agent_for,
    collect,
    replying,
    run_input,
)


async def test_history_lists_the_user_and_assistant_text_of_a_thread() -> None:
    agent = agent_for(replying("First answer.", "Second answer."))
    for text in ("one", "two"):
        await collect(agent_streaming.stream_events(agent, run_input(text), CONTEXT))

    history = await agent_threads.read_history(agent, THREAD)

    assert [(m.role, m.content) for m in history] == [
        ("user", "one"),
        ("assistant", "First answer."),
        ("user", "two"),
        ("assistant", "Second answer."),
    ]


async def test_history_leaves_out_tool_calls_and_their_results() -> None:
    model = ScriptedModel(
        replies=[
            AIMessage(
                content="",
                tool_calls=[{"name": "ls", "args": {"path": "/"}, "id": "call-1"}],
            ),
            AIMessage(content="All done."),
        ]
    )
    agent = agent_for(model)
    await collect(
        agent_streaming.stream_events(agent, run_input("look around"), CONTEXT)
    )

    history = await agent_threads.read_history(agent, THREAD)

    assert [(m.role, m.content) for m in history] == [
        ("user", "look around"),
        ("assistant", "All done."),
    ]


async def test_threads_do_not_see_each_others_history() -> None:
    agent = agent_for(replying("For the first.", "For the other."))
    await collect(
        agent_streaming.stream_events(agent, run_input("private to one"), CONTEXT)
    )
    await collect(
        agent_streaming.stream_events(
            agent, run_input("private to two", OTHER_THREAD), CONTEXT
        )
    )

    first = await agent_threads.read_history(agent, THREAD)
    other = await agent_threads.read_history(agent, OTHER_THREAD)

    assert [m.content for m in first] == ["private to one", "For the first."]
    assert [m.content for m in other] == ["private to two", "For the other."]


async def test_a_thread_that_never_ran_has_no_history() -> None:
    history = await agent_threads.read_history(agent_for(replying()), str(uuid.uuid4()))

    assert history == []


async def test_deleted_threads_are_forgotten() -> None:
    saver = InMemorySaver()
    agent = agent_factory.build_agent(replying("kept", "gone"), saver)
    await collect(agent_streaming.stream_events(agent, run_input("one"), CONTEXT))
    await collect(
        agent_streaming.stream_events(agent, run_input("two", OTHER_THREAD), CONTEXT)
    )

    await agent_threads.delete_threads(saver, [THREAD])

    assert await agent_threads.read_history(agent, THREAD) == []
    assert await agent_threads.read_history(agent, OTHER_THREAD) != []
