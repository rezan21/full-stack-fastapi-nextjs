from fastapi import APIRouter, BackgroundTasks

from src.auth import dependencies as auth_dependencies
from src.auth import service as auth_service
from src.auth.schemas import NewPassword, Token
from src.chat import dependencies as chat_dependencies
from src.chat import service as chat_service
from src.database import SessionDep
from src.exceptions import AUTH_ERRORS, error_responses
from src.models import Message
from src.users import service as users_service
from src.users.models import User
from src.users.schemas import (
    AccountDeletion,
    EmailChange,
    EmailChangeConfirm,
    UpdatePassword,
    UserPublic,
    UserRegister,
    UserUpdateMe,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup")
async def register_user(
    session: SessionDep, user_in: UserRegister, background_tasks: BackgroundTasks
) -> Message:
    """Request the link that completes a sign-up."""
    await users_service.request_signup(
        session=session,
        email=user_in.email,
        full_name=user_in.full_name,
        background_tasks=background_tasks,
    )
    return Message(message="If that email can be used, we sent a link to continue")


@router.post(
    "/signup/complete",
    response_model=UserPublic,
    status_code=201,
    responses=error_responses(400),
)
async def complete_signup(session: SessionDep, body: NewPassword) -> User:
    """Create the user a sign-up link was sent for."""
    return await users_service.complete_signup(
        session=session, token=body.token, password=body.new_password
    )


@router.get("/me", response_model=UserPublic, responses=AUTH_ERRORS)
async def read_user_me(current_user: auth_dependencies.CurrentUser) -> User:
    """Get current user."""
    return current_user


@router.patch("/me", response_model=UserPublic, responses=AUTH_ERRORS)
async def update_user_me(
    *,
    session: SessionDep,
    user_in: UserUpdateMe,
    current_user: auth_dependencies.CurrentUser,
) -> User:
    """Update own user."""
    return await users_service.update_user(session, current_user, user_in)


@router.post("/me/email", responses={**AUTH_ERRORS, **error_responses(400, 429)})
async def request_email_change(
    *,
    session: SessionDep,
    body: EmailChange,
    current_user: auth_dependencies.CurrentUser,
    background_tasks: BackgroundTasks,
) -> Message:
    """Request the link that confirms a new email address."""
    await auth_service.require_current_password(
        session, current_user, body.current_password
    )
    await users_service.request_email_change(
        session=session,
        user=current_user,
        new_email=body.email,
        background_tasks=background_tasks,
    )
    return Message(message="If that email can be used, we sent a link to confirm it")


@router.post("/confirm-email", responses=error_responses(400))
async def confirm_email_change(
    session: SessionDep, body: EmailChangeConfirm, background_tasks: BackgroundTasks
) -> Message:
    """Apply a confirmed email change."""
    previous_email, new_email = await users_service.confirm_email_change(
        session=session, token=body.token
    )
    background_tasks.add_task(
        users_service.send_email_changed_notice,
        email_to=previous_email,
        new_email=new_email,
    )
    return Message(message="Email updated successfully")


@router.patch(
    "/me/password",
    responses={**AUTH_ERRORS, **error_responses(400, 429)},
)
async def update_password_me(
    *,
    session: SessionDep,
    body: UpdatePassword,
    current_user: auth_dependencies.CurrentUser,
) -> Token:
    """Update own password."""
    await auth_service.require_current_password(
        session, current_user, body.current_password
    )
    await users_service.change_password(
        session, current_user, body.current_password, body.new_password
    )
    return auth_service.issue_token(current_user)


@router.delete(
    "/me", status_code=204, responses={**AUTH_ERRORS, **error_responses(400, 429)}
)
async def delete_user_me(
    session: SessionDep,
    body: AccountDeletion,
    current_user: auth_dependencies.CurrentUser,
    chat: chat_dependencies.ChatDep,
) -> None:
    """Delete own user."""
    await auth_service.require_current_password(
        session, current_user, body.current_password
    )
    users_service.ensure_deletable(current_user)
    await chat_service.delete_user_threads(session, current_user.id, chat.checkpointer)
    await users_service.delete_user(session, current_user)
