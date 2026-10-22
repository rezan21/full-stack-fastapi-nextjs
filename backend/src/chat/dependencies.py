import uuid
from typing import Annotated

from ag_ui.core import RunAgentInput
from ag_ui_langgraph import LangGraphAgent
from fastapi import Depends, Request

from src.auth import dependencies as auth_dependencies
from src.chat import service as chat_service
from src.chat.client import Chat
from src.chat.exceptions import ChatNotConfigured, ConversationNotFound
from src.chat.models import Conversation
from src.chat.schemas import ChatRun
from src.database import SessionDep


async def get_chat(request: Request) -> Chat:
    """Return the chat the app opened at startup."""
    chat: Chat = request.app.state.chat
    return chat


ChatDep = Annotated[Chat, Depends(get_chat)]


async def valid_chat_agent(chat: ChatDep) -> LangGraphAgent:
    """Return the chat agent, or raise a 503 when no model is configured."""
    if chat.agent is None:
        raise ChatNotConfigured()
    return chat.agent


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
    session: SessionDep, body: ChatRun, conversation: RunConversation
) -> RunAgentInput:
    """Check a run request and build the input the agent is given."""
    return await chat_service.start_run(session, conversation, body)
