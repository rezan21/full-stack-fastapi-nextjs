import uuid
from typing import Any

from ag_ui_langgraph import LangGraphAgent
from deepagents import create_deep_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.agent import streaming as agent_streaming
from src.agent.context import AgentContext
from tests.utils.agent import ScriptedModel, agent_for, collect, replying, run_input

seen: list[AgentContext] = []


@tool
def whoami(runtime: ToolRuntime[AgentContext]) -> str:
    """Say who the run is made for."""
    seen.append(runtime.context)
    return "noted"


def agent_with_tool() -> LangGraphAgent:
    calls = [{"name": "whoami", "args": {}, "id": "call-1"}]
    model = ScriptedModel(
        replies=[
            AIMessage(content="", tool_calls=calls),
            AIMessage(content="done"),
            AIMessage(content="", tool_calls=[{**calls[0], "id": "call-2"}]),
            AIMessage(content="done"),
        ]
    )
    graph = create_deep_agent(
        model=model,
        tools=[whoami],
        context_schema=AgentContext,
        checkpointer=InMemorySaver(),
    )
    return LangGraphAgent(name="test", graph=graph, emit_raw_events=False)


async def run_as(agent: LangGraphAgent, user_id: uuid.UUID, text: str) -> list[Any]:
    context = AgentContext(user_id=user_id)
    return await collect(agent_streaming.stream_events(agent, run_input(text), context))


def test_the_chat_agent_runs_with_the_context() -> None:
    assert agent_for(replying()).graph.context_schema is AgentContext


async def test_a_tool_sees_who_the_run_is_made_for() -> None:
    seen.clear()
    user_id = uuid.uuid4()

    await run_as(agent_with_tool(), user_id, "who am I")

    assert seen == [AgentContext(user_id=user_id)]


async def test_every_run_carries_its_own_user() -> None:
    seen.clear()
    agent = agent_with_tool()
    first, second = uuid.uuid4(), uuid.uuid4()

    await run_as(agent, first, "who am I")
    await run_as(agent, second, "and now")

    assert [context.user_id for context in seen] == [first, second]
