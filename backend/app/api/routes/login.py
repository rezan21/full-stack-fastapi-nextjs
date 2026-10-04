import hmac
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import SessionDep, error_responses
from app.core import security
from app.core.config import settings
from app.models import Message, NewPassword, PasswordRecovery, Token
from app.utils import (
    password_fingerprint,
    send_password_recovery_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token", responses=error_responses(400))
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests"""
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        expires_in=int(access_token_expires.total_seconds()),
    )


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
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")
