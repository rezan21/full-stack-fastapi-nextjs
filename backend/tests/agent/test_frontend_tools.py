import uuid

from ag_ui.core import EventType, TextMessageContentEvent, ToolCallStartEvent
from langgraph.checkpoint.memory import InMemorySaver

from src.agent import factory as agent_factory
from src.agent import frontend_tools as agent_frontend_tools
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from src.agent.context import AgentContext
from tests.utils.agent import (
    CONTEXT,
    THREAD,
    RecordingModel,
    collect,
    flying_to_london,
)


def test_only_the_browser_tools_the_server_defines_are_offered() -> None:
    offered = agent_frontend_tools.offered(["fly_to", "steal", "fly_to"])

    assert [tool.name for tool in offered] == ["fly_to"]


def test_a_client_that_names_no_tool_is_offered_none() -> None:
    assert agent_frontend_tools.offered([]) == []


async def test_a_browser_tool_call_ends_the_run_and_waits_for_the_browser() -> None:
    agent = agent_factory.build_agent(flying_to_london("done"), InMemorySaver())
    tools = agent_frontend_tools.offered(["fly_to"])

    events = await collect(
        agent_streaming.stream_events(
            agent, agent_streaming.build_run_input(THREAD, "r1", "go", tools), CONTEXT
        )
    )

    started = [e for e in events if isinstance(e, ToolCallStartEvent)]
    assert [e.tool_call_name for e in started] == ["fly_to"]
    assert not any(e.type == EventType.TOOL_CALL_RESULT for e in events)
    assert events[-1].type == EventType.RUN_FINISHED
    assert await agent_threads.pending_tool_call_ids(agent, THREAD) == {"call-1"}


async def test_the_browsers_answer_continues_the_run() -> None:
    agent = agent_factory.build_agent(
        flying_to_london("Now showing London."), InMemorySaver()
    )
    tools = agent_frontend_tools.offered(["fly_to"])
    first = agent_streaming.build_run_input(THREAD, "r1", "go", tools)
    await collect(agent_streaming.stream_events(agent, first, CONTEXT))

    answer = agent_streaming.build_tool_result_input(
        THREAD, "r2", "call-1", "The map now shows London.", tools
    )
    events = await collect(agent_streaming.stream_events(agent, answer, CONTEXT))

    said = "".join(e.delta for e in events if isinstance(e, TextMessageContentEvent))
    assert said == "Now showing London."
    assert await agent_threads.pending_tool_call_ids(agent, THREAD) == set()


async def test_a_call_nothing_asked_for_is_not_pending() -> None:
    agent = agent_factory.build_agent(flying_to_london("done"), InMemorySaver())

    assert await agent_threads.pending_tool_call_ids(agent, THREAD) == set()


async def test_the_model_is_not_shown_who_the_run_is_made_for() -> None:
    model = RecordingModel()
    agent = agent_factory.build_agent(model, InMemorySaver())
    user_id = uuid.uuid4()

    await collect(
        agent_streaming.stream_events(
            agent,
            agent_streaming.build_run_input(THREAD, "r1", "hello"),
            AgentContext(user_id=user_id),
        )
    )

    everything = " ".join(str(m.content) for m in model.seen[0])
    assert str(user_id) not in everything
    assert "App Context" not in everything
