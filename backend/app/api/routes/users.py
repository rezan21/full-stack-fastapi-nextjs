from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app import crud
from app.api.deps import AUTH_ERRORS, CurrentUser, SessionDep, error_responses
from app.core import security
from app.core.security import get_password_hash, verify_password
from app.models import (
    AccountDeletion,
    EmailChange,
    EmailChangeConfirm,
    Message,
    NewPassword,
    Token,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UserUpdateMe,
)
from app.utils import (
    EMAIL_CHANGE_AUDIENCE,
    SIGNUP_AUDIENCE,
    send_email_change_email,
    send_email_change_requested_notice,
    send_email_changed_notice,
    send_signup_email,
    verify_email_token,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup")
def register_user(
    session: SessionDep, user_in: UserRegister, background_tasks: BackgroundTasks
) -> Message:
    """Request the link that completes a sign-up."""
    if not crud.get_user_by_email(session=session, email=user_in.email):
        background_tasks.add_task(
            send_signup_email, email_to=user_in.email, full_name=user_in.full_name
        )
    return Message(message="If that email can be used, we sent a link to continue")


@router.post(
    "/signup/complete",
    response_model=UserPublic,
    status_code=201,
    responses=error_responses(400),
)
def complete_signup(session: SessionDep, body: NewPassword) -> Any:
    """Create the user a sign-up link was sent for."""
    claims = verify_email_token(body.token, audience=SIGNUP_AUDIENCE)
    if not claims or crud.get_user_by_email(session=session, email=claims["sub"]):
        raise HTTPException(status_code=400, detail="Invalid token")
    user_create = UserCreate(
        email=claims["sub"], full_name=claims["name"], password=body.new_password
    )
    return crud.create_user(session=session, user_create=user_create)


@router.get("/me", response_model=UserPublic, responses=AUTH_ERRORS)
def read_user_me(current_user: CurrentUser) -> Any:
    """Get current user."""
    return current_user


@router.patch("/me", response_model=UserPublic, responses=AUTH_ERRORS)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""

    current_user.sqlmodel_update(user_in.model_dump(exclude_unset=True))
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.post("/me/email", responses={**AUTH_ERRORS, **error_responses(400)})
def request_email_change(
    *,
    session: SessionDep,
    body: EmailChange,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> Message:
    """Request the link that confirms a new email address."""
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    background_tasks.add_task(
        send_email_change_requested_notice,
        email_to=current_user.email,
        new_email=body.email,
    )
    if not crud.get_user_by_email(session=session, email=body.email):
        background_tasks.add_task(
            send_email_change_email,
            email_to=body.email,
            user_id=current_user.id,
            current_email=current_user.email,
        )
    return Message(message="If that email can be used, we sent a link to confirm it")


@router.post("/confirm-email", responses=error_responses(400))
def confirm_email_change(
    session: SessionDep, body: EmailChangeConfirm, background_tasks: BackgroundTasks
) -> Message:
    """Apply a confirmed email change."""
    claims = verify_email_token(body.token, audience=EMAIL_CHANGE_AUDIENCE)
    user = session.get(User, claims["sub"]) if claims else None
    if (
        not claims
        or not user
        or user.email != claims["from"]
        or crud.get_user_by_email(session=session, email=claims["email"])
    ):
        raise HTTPException(status_code=400, detail="Invalid token")
    previous_email = user.email
    user.email = claims["email"]
    crud.revoke_tokens(user)
    session.add(user)
    session.commit()
    background_tasks.add_task(
        send_email_changed_notice, email_to=previous_email, new_email=user.email
    )
    return Message(message="Email updated successfully")


@router.patch(
    "/me/password",
    response_model=Token,
    responses={**AUTH_ERRORS, **error_responses(400)},
)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    current_user.hashed_password = get_password_hash(body.new_password)
    crud.revoke_tokens(current_user)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return security.issue_token(current_user)


@router.delete(
    "/me", status_code=204, responses={**AUTH_ERRORS, **error_responses(400)}
)
def delete_user_me(
    session: SessionDep, body: AccountDeletion, current_user: CurrentUser
) -> None:
    """Delete own user."""
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
