import uuid
from datetime import timedelta

from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import utils as auth_utils
from src.auth.exceptions import InvalidToken
from src.config import settings
from src.notifications import service as notifications_service
from src.users import constants as users_constants
from src.users.config import users_settings
from src.users.exceptions import PasswordUnchanged, SuperuserCannotDelete
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdateMe


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    """Create a user."""
    hashed_password = await run_in_threadpool(
        auth_utils.get_password_hash, user_create.password
    )
    db_obj = User.model_validate(
        user_create, update={"hashed_password": hashed_password}
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Return the user with the email, or None."""
    statement = select(User).where(User.email == email.lower())
    session_user = (await session.exec(statement)).first()
    return session_user


async def request_signup(
    *,
    session: AsyncSession,
    email: str,
    full_name: str,
    background_tasks: BackgroundTasks,
) -> None:
    """Schedule the sign-up link unless the address already has an account."""
    if not await get_user_by_email(session=session, email=email):
        background_tasks.add_task(
            send_signup_email, email_to=email, full_name=full_name
        )


async def request_email_change(
    *,
    session: AsyncSession,
    user: User,
    new_email: str,
    background_tasks: BackgroundTasks,
) -> None:
    """Notify the current address and, when the new one is free, send it the confirmation link."""
    background_tasks.add_task(
        send_email_change_requested_notice, email_to=user.email, new_email=new_email
    )
    if not await get_user_by_email(session=session, email=new_email):
        background_tasks.add_task(
            send_email_change_email,
            email_to=new_email,
            user_id=user.id,
            current_email=user.email,
        )


def revoke_tokens(user: User) -> None:
    """Retire every token issued to the user; the caller commits."""
    user.token_version += 1


async def complete_signup(*, session: AsyncSession, token: str, password: str) -> User:
    """Create the user a sign-up link was sent for."""
    claims = auth_utils.verify_email_token(
        token, audience=users_constants.SIGNUP_AUDIENCE
    )
    if not claims or await get_user_by_email(session=session, email=claims["sub"]):
        raise InvalidToken()
    user_create = UserCreate(
        email=claims["sub"], full_name=claims["name"], password=password
    )
    try:
        return await create_user(session=session, user_create=user_create)
    except IntegrityError:
        await session.rollback()
        raise InvalidToken()


async def update_user(session: AsyncSession, user: User, user_in: UserUpdateMe) -> User:
    """Apply the fields the user sent."""
    user.sqlmodel_update(user_in.model_dump(exclude_unset=True))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def confirm_email_change(*, session: AsyncSession, token: str) -> tuple[str, str]:
    """Apply a confirmed email change, returning the previous and the new address."""
    claims = auth_utils.verify_email_token(
        token, audience=users_constants.EMAIL_CHANGE_AUDIENCE
    )
    user = await session.get(User, claims["sub"]) if claims else None
    if (
        not claims
        or not user
        or user.email != claims["from"]
        or await get_user_by_email(session=session, email=claims["email"])
    ):
        raise InvalidToken()
    previous_email = user.email
    user.email = claims["email"]
    revoke_tokens(user)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise InvalidToken()
    return previous_email, user.email


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    """Set a new password and retire every token issued to the user."""
    if current_password == new_password:
        raise PasswordUnchanged()
    user.hashed_password = await run_in_threadpool(
        auth_utils.get_password_hash, new_password
    )
    revoke_tokens(user)
    session.add(user)
    await session.commit()
    await session.refresh(user)


def ensure_deletable(user: User) -> None:
    """Raise when the user is not allowed to delete their own account."""
    if user.is_superuser:
        raise SuperuserCannotDelete()


async def delete_user(session: AsyncSession, user: User) -> None:
    """Delete the user."""
    await session.delete(user)
    await session.commit()


def send_signup_email(*, email_to: str, full_name: str) -> None:
    """Send the link that completes a sign-up."""
    token = auth_utils.generate_email_token(
        audience=users_constants.SIGNUP_AUDIENCE,
        claims={"sub": email_to, "name": full_name},
        expires_in=timedelta(minutes=users_settings.SIGNUP_TOKEN_EXPIRE_MINUTES),
    )
    notifications_service.send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your email",
        message=f"Confirm your email address to finish creating your {settings.PROJECT_NAME} account:",
        path="/signup/complete",
        token=token,
        valid_minutes=users_settings.SIGNUP_TOKEN_EXPIRE_MINUTES,
    )


def send_email_change_email(
    *, email_to: str, user_id: uuid.UUID, current_email: str
) -> None:
    """Send the link that confirms a new email address."""
    token = auth_utils.generate_email_token(
        audience=users_constants.EMAIL_CHANGE_AUDIENCE,
        claims={"sub": str(user_id), "email": email_to, "from": current_email},
        expires_in=timedelta(minutes=users_settings.EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES),
    )
    notifications_service.send_confirmation_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Confirm your new email",
        message=f"Confirm this address to use it for your {settings.PROJECT_NAME} account:",
        path="/confirm-email",
        token=token,
        valid_minutes=users_settings.EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES,
    )


def send_email_change_requested_notice(*, email_to: str, new_email: str) -> None:
    """Tell the current address that a change to a new address was requested."""
    notifications_service.send_notice_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Email change requested",
        message=(
            f"A change of the email address of your {settings.PROJECT_NAME} account "
            f"to {new_email} was requested. If this was you, confirm it from the "
            "link we sent to that address. If it was not, change your password now."
        ),
    )


def send_email_changed_notice(*, email_to: str, new_email: str) -> None:
    """Tell the previous address that the account now uses a new address."""
    notifications_service.send_notice_email(
        email_to=email_to,
        subject=f"{settings.PROJECT_NAME} - Your email was changed",
        message=(
            f"The email address of your {settings.PROJECT_NAME} account was changed "
            f"to {new_email}, and every session was signed out. If this was not you, "
            "your account may be compromised: contact the site operator."
        ),
    )
