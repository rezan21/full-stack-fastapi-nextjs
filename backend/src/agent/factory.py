from typing import Any

from ag_ui_langgraph import LangGraphAgent
from deepagents import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from pydantic import SecretStr

from src.agent.context import AgentContext
from src.agent.notes import NOTES_PROMPT

MAX_OUTPUT_TOKENS = 8192
MODEL_TIMEOUT_SECONDS = 60
MODEL_MAX_RETRIES = 2
RECURSION_LIMIT = 30
SYSTEM_PROMPT = f"You are a helpful assistant. Keep answers concise. {NOTES_PROMPT}"


def build_model(api_key: SecretStr, name: str) -> ChatOpenAI:
    """Build the OpenAI chat model with bounded output, time and retries."""
    return ChatOpenAI(
        model=name,
        api_key=api_key,
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_MAX_RETRIES,
        use_responses_api=False,
        store=False,
    )


def build_agent(
    model: BaseChatModel, checkpointer: BaseCheckpointSaver[Any]
) -> LangGraphAgent:
    """Build the chat agent over the model, remembering conversations in the checkpointer."""
    graph = create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        context_schema=AgentContext,
        checkpointer=checkpointer,
        name="chat",
    )
    return LangGraphAgent(
        name="chat",
        graph=graph,  # ty: ignore[invalid-argument-type]
        config={"recursion_limit": RECURSION_LIMIT},
        emit_raw_events=False,
    )
