import hmac
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException

from app import crud
from app.api.deps import (
    AUTH_ERRORS,
    CurrentUser,
    SessionDep,
    ensure_not_locked,
    error_responses,
)
from app.core import security, throttle
from app.models import Credentials, Message, NewPassword, PasswordRecovery, Token
from app.utils import (
    password_fingerprint,
    send_password_recovery_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token", responses=error_responses(400, 429))
def login_access_token(
    session: SessionDep, form_data: Annotated[Credentials, Form()]
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests"""
    ensure_not_locked(session, form_data.username)
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        throttle.record_failure(session, form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    throttle.clear(session, form_data.username)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return security.issue_token(user)


@router.post("/logout", status_code=204, responses=AUTH_ERRORS)
def logout(session: SessionDep, current_user: CurrentUser) -> None:
    """Sign the user out everywhere by retiring their tokens."""
    crud.revoke_tokens(current_user)
    session.add(current_user)
    session.commit()


@router.post("/password-recovery")
def recover_password(
    body: PasswordRecovery, session: SessionDep, background_tasks: BackgroundTasks
) -> Message:
    """Password Recovery"""
    user = crud.get_user_by_email(session=session, email=body.email)

    if user:
        background_tasks.add_task(
            send_password_recovery_email,
            email_to=user.email,
            email=body.email,
            hashed_password=user.hashed_password,
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password", responses=error_responses(400))
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Reset password"""
    claims = verify_password_reset_token(token=body.token)
    if not claims:
        raise HTTPException(status_code=400, detail="Invalid token")
    email, fingerprint = claims
    user = crud.get_user_by_email(session=session, email=email)
    if not user or not hmac.compare_digest(
        password_fingerprint(user.hashed_password), fingerprint
    ):
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user.hashed_password = security.get_password_hash(body.new_password)
    crud.revoke_tokens(user)
    session.add(user)
    session.commit()
    throttle.clear(session, user.email)
    return Message(message="Password updated successfully")
