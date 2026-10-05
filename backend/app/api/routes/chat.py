import uuid
from collections.abc import AsyncIterable
from functools import partial
from math import ceil
from typing import Annotated, Any

from ag_ui.core import RunAgentInput
from ag_ui_langgraph import LangGraphAgent
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlmodel import Session, col, func, select

from app.api.deps import AUTH_ERRORS, ChatDep, CurrentUser, SessionDep, error_responses
from app.core import chat_limit, transcript
from app.core.chat import (
    Chat,
    ChatInputError,
    build_run_input,
    conversation_title,
    record_replies,
    stream_events,
)
from app.core.transcript import AgentMessage
from app.models import (
    ChatMessagePublic,
    ChatMessagesPublic,
    ChatRun,
    Conversation,
    ConversationPublic,
    ConversationsPublic,
    get_datetime_utc,
)
from app.utils import describe_duration

router = APIRouter(prefix="/chat", tags=["chat"], responses=AUTH_ERRORS)

MAX_PAGE_SIZE = 100
MESSAGES_PAGE_SIZE = 100
MAX_MESSAGES_PAGE_SIZE = 500


def configured_agent(chat: Chat) -> LangGraphAgent:
    """Return the chat agent, or raise a 503 when no model is configured."""
    if chat.agent is None:
        raise HTTPException(status_code=503, detail="AI chat is not configured")
    return chat.agent


def find_owned(
    session: Session, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation | None:
    """Return the conversation when it belongs to the user."""
    return session.exec(
        select(Conversation).where(
            col(Conversation.id) == conversation_id,
            col(Conversation.owner_id) == user_id,
        )
    ).first()


def get_owned_conversation(
    id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Conversation:
    """Return the conversation, raising a 404 unless it belongs to the current user."""
    conversation = find_owned(session, current_user.id, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


OwnedConversation = Annotated[Conversation, Depends(get_owned_conversation)]


def prepare_run(
    session: SessionDep, current_user: CurrentUser, body: ChatRun, chat: ChatDep
) -> RunAgentInput:
    """Check a run request and build the input the agent is given."""
    configured_agent(chat)
    user_id = current_user.id
    try:
        conversation_id = uuid.UUID(body.thread_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation = find_owned(session, user_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        run_input = build_run_input(body, conversation_id)
    except ChatInputError as error:
        raise HTTPException(status_code=400, detail=str(error))
    try:
        chat_limit.count_run(session, user_id)
    except chat_limit.TooManyRuns as error:
        raise HTTPException(
            status_code=429,
            detail=f"Too many messages. Try again in {describe_duration(ceil(error.retry_after / 60))}.",
            headers={"Retry-After": str(error.retry_after)},
        )
    message = run_input.messages[0]
    transcript.add_messages(
        session,
        conversation_id,
        [AgentMessage(id=message.id, role="user", content=str(message.content))],
    )
    conversation.updated_at = get_datetime_utc()
    if conversation.title is None:
        conversation.title = conversation_title(str(message.content))
    session.add(conversation)
    session.commit()
    session.close()
    return run_input


@router.post("/conversations", response_model=ConversationPublic, status_code=201)
def create_conversation(session: SessionDep, current_user: CurrentUser) -> Any:
    """Start a new conversation."""
    conversation = Conversation(owner_id=current_user.id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=ConversationsPublic)
def read_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = MAX_PAGE_SIZE,
) -> Any:
    """Retrieve the current user's conversations, latest activity first."""
    owned = col(Conversation.owner_id) == current_user.id
    count = session.exec(
        select(func.count()).select_from(Conversation).where(owned)
    ).one()
    conversations = session.exec(
        select(Conversation)
        .where(owned)
        .order_by(col(Conversation.updated_at).desc(), col(Conversation.id))
        .offset(skip)
        .limit(limit)
    ).all()
    return ConversationsPublic(
        data=[ConversationPublic.model_validate(c) for c in conversations],
        count=count,
    )


@router.get(
    "/conversations/{id}",
    response_model=ConversationPublic,
    responses=error_responses(404),
)
def read_conversation(conversation: OwnedConversation) -> Any:
    """Get a conversation by ID."""
    return conversation


@router.get(
    "/conversations/{id}/messages",
    response_model=ChatMessagesPublic,
    responses=error_responses(404),
)
def read_messages(
    conversation: OwnedConversation,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=MAX_MESSAGES_PAGE_SIZE)] = MESSAGES_PAGE_SIZE,
) -> Any:
    """Get what was said in a conversation, latest messages last."""
    messages, count = transcript.read_messages(session, conversation.id, limit)
    return ChatMessagesPublic(
        data=[ChatMessagePublic.model_validate(m) for m in messages], count=count
    )


@router.post(
    "",
    response_class=EventSourceResponse,
    responses=error_responses(400, 404, 429, 503),
)
async def run_chat(
    run_input: Annotated[RunAgentInput, Depends(prepare_run)], chat: ChatDep
) -> AsyncIterable[ServerSentEvent]:
    """Stream the assistant's reply to a message as AG-UI events."""
    agent = configured_agent(chat)
    on_finished = partial(record_replies, agent, run_input)
    async for event in stream_events(agent, run_input, on_finished):
        yield ServerSentEvent(raw_data=event.model_dump_json(by_alias=True))
