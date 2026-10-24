from typing import Any

from ag_ui.core import Interrupt, ResumeEntry
from ag_ui_langgraph import LangGraphAgent
from copilotkit import LangGraphAGUIAgent
from deepagents import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import SecretStr

from src.agent import interrupts as agent_interrupts
from src.agent.browser import BrowserToolsMiddleware
from src.agent.context import AgentContext
from src.agent.notes import NOTES_PROMPT
from src.agent.tools.registry import SERVER_TOOLS

MAX_OUTPUT_TOKENS = 8192
MODEL_TIMEOUT_SECONDS = 60
MODEL_MAX_RETRIES = 2
RECURSION_LIMIT = 30
SYSTEM_PROMPT = f"You are a helpful assistant. Keep answers concise. {NOTES_PROMPT}"


class ChatAgent(LangGraphAGUIAgent):
    """AG-UI agent that answers each open interrupt with the user's answer and keeps raw LangGraph events off the wire."""

    def __init__(
        self,
        *,
        name: str,
        graph: CompiledStateGraph[Any, Any, Any, Any],
        description: str | None = None,
        config: RunnableConfig | None = None,
        emit_raw_events: bool = False,
        emit_interrupt_outcome: bool = True,
        enable_legacy_on_interrupt_event: bool = False,
    ) -> None:
        super().__init__(name=name, graph=graph, description=description, config=config)
        self.emit_raw_events = emit_raw_events
        self.emit_interrupt_outcome = emit_interrupt_outcome
        self.enable_legacy_on_interrupt_event = enable_legacy_on_interrupt_event

    def _build_command_from_agui_resume(
        self,
        entries: list[ResumeEntry],
        *,
        open_interrupts: list[Interrupt] | None = None,
    ) -> Command[Any]:
        return Command(
            resume={
                entry.interrupt_id: agent_interrupts.resume_value(entry)
                for entry in entries
            }
        )


def build_model(api_key: SecretStr, name: str) -> ChatOpenAI:
    """Build the OpenAI chat model with bounded output, time and retries, calling one tool at a time."""
    return ChatOpenAI(
        model=name,
        api_key=api_key,
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_MAX_RETRIES,
        use_responses_api=False,
        store=False,
        model_kwargs={"parallel_tool_calls": False},
    )


def build_agent(
    model: BaseChatModel, checkpointer: BaseCheckpointSaver[Any]
) -> LangGraphAgent:
    """Build the chat agent over the model, remembering conversations in the checkpointer."""
    graph = create_deep_agent(
        model=model,
        tools=SERVER_TOOLS,
        middleware=[BrowserToolsMiddleware()],
        system_prompt=SYSTEM_PROMPT,
        context_schema=AgentContext,
        checkpointer=checkpointer,
        name="chat",
    )
    return ChatAgent(
        name="chat",
        graph=graph,
        config={"recursion_limit": RECURSION_LIMIT},
    )
