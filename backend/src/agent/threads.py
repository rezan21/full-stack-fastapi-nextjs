from collections.abc import Iterable
from typing import Any, Literal, NamedTuple

from ag_ui_langgraph import LangGraphAgent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agent.interrupts import UNANSWERED_RESULT
from src.agent.notes import is_app_note
from src.agent.schemas import AgentMessage


class OpenInterrupt(NamedTuple):
    """A pause in which the agent waits for the user's answer."""

    interrupt_id: str
    node: str
    tool_call_id: str | None


def thread_config(thread_id: str) -> RunnableConfig:
    """Return the agent's config for a thread."""
    return {"configurable": {"thread_id": thread_id}}


def agent_message(message: BaseMessage) -> AgentMessage | None:
    """Return the message as the user would read it, or None when it has no text for them."""
    role: Literal["user", "assistant"]
    if is_app_note(message):
        return None
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    else:
        return None
    text = str(message.text)
    if message.id is None or not text.strip():
        return None
    return AgentMessage(id=message.id, role=role, content=text)


async def read_history(agent: LangGraphAgent, thread_id: str) -> list[AgentMessage]:
    """Return what the user and the assistant said, as the agent remembers it."""
    state = await agent.graph.aget_state(thread_config(thread_id))
    messages = (state.values or {}).get("messages", [])
    shown = (agent_message(message) for message in messages)
    return [message for message in shown if message is not None]


async def open_interrupts(agent: LangGraphAgent, thread_id: str) -> list[OpenInterrupt]:
    """Return the interrupts the agent is waiting on the user to answer."""
    state = await agent.graph.aget_state(thread_config(thread_id))
    return [
        OpenInterrupt(interrupt.id, task.name, interrupt.value.get("toolCallId"))
        for task in state.tasks
        for interrupt in task.interrupts
        if interrupt.id and isinstance(interrupt.value, dict)
    ]


async def pending_tool_call_ids(agent: LangGraphAgent, thread_id: str) -> set[str]:
    """Return the ids of the agent's latest tool calls that nothing has answered yet."""
    state = await agent.graph.aget_state(thread_config(thread_id))
    messages = (state.values or {}).get("messages", [])
    with_results = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    latest = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    called = {
        call["id"] for call in (latest.tool_calls if latest else []) if call["id"]
    }
    return called - with_results


async def interrupted_tool_call_ids(
    agent: LangGraphAgent, thread_id: str, interrupt_ids: set[str]
) -> set[str]:
    """Return the ids of the tool calls that the interrupts with these ids are waiting on."""
    if not interrupt_ids:
        return set()
    return {
        interrupt.tool_call_id
        for interrupt in await open_interrupts(agent, thread_id)
        if interrupt.interrupt_id in interrupt_ids and interrupt.tool_call_id
    }


async def cancel_pending_calls(agent: LangGraphAgent, thread_id: str) -> None:
    """Answer the tool calls the agent is waiting on as unanswered, so the thread can take a new message."""
    pending = await pending_tool_call_ids(agent, thread_id)
    if not pending:
        return
    interrupts = await open_interrupts(agent, thread_id)
    unanswered = [
        ToolMessage(content=UNANSWERED_RESULT, tool_call_id=call_id)
        for call_id in sorted(pending)
    ]
    await agent.graph.aupdate_state(
        thread_config(thread_id),
        {"messages": unanswered},
        as_node=interrupts[0].node if interrupts else None,
    )


async def delete_threads(
    checkpointer: BaseCheckpointSaver[Any], thread_ids: Iterable[str]
) -> None:
    """Forget everything stored for the threads."""
    for thread_id in thread_ids:
        await checkpointer.adelete_thread(thread_id)
