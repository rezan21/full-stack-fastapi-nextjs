from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form

from src.auth import service as auth_service
from src.auth.dependencies import CurrentUser
from src.auth.schemas import Credentials, NewPassword, PasswordRecovery, Token
from src.database import SessionDep
from src.exceptions import AUTH_ERRORS, error_responses
from src.models import Message

router = APIRouter(tags=["login"])


@router.post("/login/access-token", responses=error_responses(400, 429))
async def login_access_token(
    session: SessionDep, form_data: Annotated[Credentials, Form()]
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests"""
    return await auth_service.login(
        session=session, email=form_data.username, password=form_data.password
    )


@router.post("/logout", status_code=204, responses=AUTH_ERRORS)
async def logout(session: SessionDep, current_user: CurrentUser) -> None:
    """Sign the user out everywhere by retiring their tokens."""
    await auth_service.logout(session, current_user)


@router.post("/password-recovery")
async def recover_password(
    body: PasswordRecovery, session: SessionDep, background_tasks: BackgroundTasks
) -> Message:
    """Password Recovery"""
    await auth_service.request_password_recovery(
        session=session, email=body.email, background_tasks=background_tasks
    )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password", responses=error_responses(400))
async def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Reset password"""
    await auth_service.reset_password(session, body.token, body.new_password)
    return Message(message="Password updated successfully")
