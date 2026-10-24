from collections.abc import Iterable
from typing import Any, Literal

from ag_ui_langgraph import LangGraphAgent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agent.notes import is_app_note
from src.agent.schemas import AgentMessage


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


async def delete_threads(
    checkpointer: BaseCheckpointSaver[Any], thread_ids: Iterable[str]
) -> None:
    """Forget everything stored for the threads."""
    for thread_id in thread_ids:
        await checkpointer.adelete_thread(thread_id)
