from datetime import timedelta

import pytest
from httpx import AsyncClient, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import service as auth_service
from src.auth.config import auth_settings
from src.auth.utils import generate_password_reset_token
from src.config import settings
from src.models import get_datetime_utc
from src.users import service as users_service
from src.users.schemas import UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

LOGIN = f"{settings.API_V1_STR}/login/access-token"
USERS = f"{settings.API_V1_STR}/users"


async def make_user(db: AsyncSession) -> tuple[str, str]:
    email, password = random_email(), random_lower_string()
    await users_service.create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    return email, password


async def log_in(client: AsyncClient, email: str, password: str) -> Response:
    response: Response = await client.post(
        LOGIN, data={"username": email, "password": password}
    )
    return response


async def fail_login(client: AsyncClient, email: str, times: int) -> None:
    for _ in range(times):
        assert (await log_in(client, email, "wrong-password")).status_code == 400


def advance(monkeypatch: pytest.MonkeyPatch, minutes: int) -> None:
    now = get_datetime_utc()
    monkeypatch.setattr(
        auth_service, "get_datetime_utc", lambda: now + timedelta(minutes=minutes)
    )


async def test_account_locks_after_repeated_failures_even_for_the_right_password(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = await make_user(db)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES)

    response = await log_in(client, email, password)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) <= auth_settings.AUTH_LOCK_MINUTES * 60
    assert "Try again in 15 minutes" in response.json()["detail"]


async def test_an_unknown_email_is_locked_exactly_like_a_known_one(
    client: AsyncClient, db: AsyncSession
) -> None:
    known, password = await make_user(db)
    unknown = random_email()
    await fail_login(client, known, auth_settings.AUTH_MAX_FAILURES)
    await fail_login(client, unknown, auth_settings.AUTH_MAX_FAILURES)

    locked_known = await log_in(client, known, password)
    locked_unknown = await log_in(client, unknown, "anything")

    assert locked_known.status_code == locked_unknown.status_code == 429
    assert locked_known.json() == locked_unknown.json()


async def test_a_failure_on_one_account_does_not_lock_another(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, _ = await make_user(db)
    other, other_password = await make_user(db)
    await fail_login(client, random_email(), auth_settings.AUTH_MAX_FAILURES)

    assert (await log_in(client, other, other_password)).status_code == 200


async def test_a_successful_login_resets_the_count(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = await make_user(db)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES - 1)
    assert (await log_in(client, email, password)).status_code == 200

    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES - 1)

    assert (await log_in(client, email, password)).status_code == 200


async def test_the_lock_expires(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email, password = await make_user(db)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES)
    assert (await log_in(client, email, password)).status_code == 429

    advance(monkeypatch, auth_settings.AUTH_LOCK_MINUTES + 1)

    assert (await log_in(client, email, password)).status_code == 200


async def test_old_failures_stop_counting(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email, password = await make_user(db)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES - 1)

    advance(monkeypatch, auth_settings.AUTH_LOCK_MINUTES + 1)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES - 1)

    assert (await log_in(client, email, password)).status_code == 200


async def test_wrong_current_passwords_lock_every_password_check_and_login(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = await make_user(db)
    headers = await user_authentication_headers(
        client=client, email=email, password=password
    )
    for _ in range(auth_settings.AUTH_MAX_FAILURES):
        response = await client.patch(
            f"{USERS}/me/password",
            headers=headers,
            json={"current_password": "wrong-password", "new_password": "new-password"},
        )
        assert response.status_code == 400

    right = {"current_password": password, "new_password": "new-password"}
    assert (
        await client.patch(f"{USERS}/me/password", headers=headers, json=right)
    ).status_code == 429
    assert (
        await client.post(
            f"{USERS}/me/email",
            headers=headers,
            json={"email": random_email(), "current_password": password},
        )
    ).status_code == 429
    assert (
        await client.request(
            "DELETE",
            f"{USERS}/me",
            headers=headers,
            json={"current_password": password},
        )
    ).status_code == 429
    assert (await log_in(client, email, password)).status_code == 429


async def test_resetting_the_password_unlocks_the_account(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = await make_user(db)
    await fail_login(client, email, auth_settings.AUTH_MAX_FAILURES)
    user = await users_service.get_user_by_email(session=db, email=email)
    assert user
    token = generate_password_reset_token(email, user.hashed_password)

    reset = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": "brand-new-password"},
    )

    assert reset.status_code == 200
    assert (await log_in(client, email, "brand-new-password")).status_code == 200
