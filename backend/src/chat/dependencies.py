import uuid
from typing import Annotated

from ag_ui.core import RunAgentInput
from ag_ui_langgraph import LangGraphAgent
from fastapi import Depends

from src.agent import dependencies as agent_dependencies
from src.auth import dependencies as auth_dependencies
from src.chat import service as chat_service
from src.chat.exceptions import ChatNotConfigured, ConversationNotFound
from src.chat.models import Conversation
from src.chat.schemas import ChatRun
from src.database import SessionDep


async def valid_chat_agent(runtime: agent_dependencies.RuntimeDep) -> LangGraphAgent:
    """Return the chat agent, or raise a 503 when no model is configured."""
    if runtime.agent is None:
        raise ChatNotConfigured()
    return runtime.agent


AgentDep = Annotated[LangGraphAgent, Depends(valid_chat_agent)]


async def valid_owned_conversation(
    conversation_id: uuid.UUID,
    session: SessionDep,
    current_user: auth_dependencies.CurrentUser,
) -> Conversation:
    """Return the conversation, raising a 404 unless it belongs to the current user."""
    return await chat_service.get_owned_conversation(
        session, current_user.id, conversation_id
    )


OwnedConversation = Annotated[Conversation, Depends(valid_owned_conversation)]


async def valid_run_conversation(
    body: ChatRun, session: SessionDep, current_user: auth_dependencies.CurrentUser
) -> Conversation:
    """Return the conversation a run request names, raising a 404 unless it belongs to the current user."""
    try:
        conversation_id = uuid.UUID(body.thread_id)
    except ValueError:
        raise ConversationNotFound()
    return await chat_service.get_owned_conversation(
        session, current_user.id, conversation_id
    )


RunConversation = Annotated[Conversation, Depends(valid_run_conversation)]


async def prepare_run(
    session: SessionDep,
    body: ChatRun,
    conversation: RunConversation,
    agent: AgentDep,
) -> RunAgentInput:
    """Check a run request and build the input the agent is given."""
    return await chat_service.start_run(session, conversation, body, agent)
