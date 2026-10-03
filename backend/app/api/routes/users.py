from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import AUTH_ERRORS, CurrentUser, SessionDep, error_responses
from app.core.security import get_password_hash, verify_password
from app.models import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UserUpdateMe,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=201,
    responses=error_responses(400),
)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/me", response_model=UserPublic, responses=AUTH_ERRORS)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserPublic,
    responses={**AUTH_ERRORS, **error_responses(409)},
)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    user_data = user_in.model_dump(exclude_unset=True)
    if email := user_data.get("email"):
        existing_user = crud.get_user_by_email(session=session, email=email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch(
    "/me/password",
    response_model=Message,
    responses={**AUTH_ERRORS, **error_responses(400)},
)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.delete("/me", status_code=204, responses=AUTH_ERRORS)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> None:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
