from collections.abc import AsyncIterable
from functools import partial
from typing import Annotated

from ag_ui.core import RunAgentInput
from fastapi import APIRouter, Depends, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.agent import streaming as agent_streaming
from src.agent.context import AgentContext
from src.auth import dependencies as auth_dependencies
from src.chat import service as chat_service
from src.chat.dependencies import (
    AgentDep,
    OwnedConversation,
    prepare_run,
    valid_chat_agent,
)
from src.chat.models import Conversation
from src.chat.schemas import (
    ChatMessagesPublic,
    ConversationPublic,
    ConversationsPublic,
)
from src.database import SessionDep
from src.exceptions import AUTH_ERRORS, error_responses
from src.pagination import PaginationDep

MESSAGES_PAGE_SIZE = 100
MAX_MESSAGES_PAGE_SIZE = 500

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(auth_dependencies.get_current_user)],
    responses=AUTH_ERRORS,
)


@router.post("/conversations", response_model=ConversationPublic, status_code=201)
async def create_conversation(
    session: SessionDep, current_user: auth_dependencies.CurrentUser
) -> Conversation:
    """Start a new conversation."""
    return await chat_service.create_conversation(session, current_user.id)


@router.get("/conversations", response_model=ConversationsPublic)
async def read_conversations(
    session: SessionDep,
    current_user: auth_dependencies.CurrentUser,
    pagination: PaginationDep,
) -> dict[str, object]:
    """Retrieve the current user's conversations, latest activity first."""
    conversations, count = await chat_service.list_conversations(
        session, current_user.id, pagination
    )
    return {"data": conversations, "count": count}


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationPublic,
    responses=error_responses(404),
)
async def read_conversation(conversation: OwnedConversation) -> Conversation:
    """Get a conversation by ID."""
    return conversation


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessagesPublic,
    responses=error_responses(404),
)
async def read_messages(
    conversation: OwnedConversation,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=MAX_MESSAGES_PAGE_SIZE)] = (
        MESSAGES_PAGE_SIZE
    ),
) -> dict[str, object]:
    """Get what was said in a conversation, latest messages last."""
    messages, count = await chat_service.read_messages(session, conversation.id, limit)
    return {"data": messages, "count": count}


@router.post(
    "",
    response_class=EventSourceResponse,
    dependencies=[Depends(valid_chat_agent)],
    responses=error_responses(400, 404, 429, 503),
)
async def run_chat(
    run_input: Annotated[RunAgentInput, Depends(prepare_run)],
    agent: AgentDep,
    current_user: auth_dependencies.CurrentUser,
) -> AsyncIterable[ServerSentEvent]:
    """Stream the assistant's reply to a message as AG-UI events."""
    context = AgentContext(user_id=current_user.id)
    on_finished = partial(chat_service.record_replies, agent, run_input)
    async for event in agent_streaming.stream_events(
        agent, run_input, context, on_finished
    ):
        yield ServerSentEvent(raw_data=event.model_dump_json(by_alias=True))
