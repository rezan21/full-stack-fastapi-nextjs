from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from httpx import AsyncClient
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.config import auth_settings
from src.auth.constants import ALGORITHM
from src.auth.utils import (
    generate_password_reset_token,
    get_password_hash,
    verify_password,
)
from src.config import settings
from src.users.config import users_settings
from src.users.models import User
from src.users.schemas import UserCreate
from src.users.service import create_user
from tests.utils.user import user_authentication_headers
from tests.utils.utils import EMAIL_TEST_USER, random_email, random_lower_string


async def test_get_access_token(client: AsyncClient) -> None:
    login_data = {
        "username": users_settings.FIRST_SUPERUSER,
        "password": users_settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]
    assert tokens["expires_in"] == auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def test_login_ignores_the_oauth_fields_a_client_may_send(
    client: AsyncClient,
) -> None:
    login_data = {
        "username": users_settings.FIRST_SUPERUSER,
        "password": users_settings.FIRST_SUPERUSER_PASSWORD,
        "grant_type": "password",
        "scope": "",
        "client_id": "unused",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200


async def test_login_username_is_case_insensitive(client: AsyncClient) -> None:
    login_data = {
        "username": users_settings.FIRST_SUPERUSER.upper(),
        "password": users_settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200


@pytest.mark.parametrize(
    "login_data",
    [
        {"username": "not-an-email", "password": "x"},
        {"username": users_settings.FIRST_SUPERUSER, "password": ""},
        {"username": users_settings.FIRST_SUPERUSER},
    ],
)
async def test_login_rejects_credentials_the_contract_rejects(
    client: AsyncClient, login_data: dict[str, str]
) -> None:
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 422


async def test_get_access_token_incorrect_password(client: AsyncClient) -> None:
    login_data = {
        "username": users_settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


async def test_recovery_password(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch(
            "src.notifications.config.notifications_settings.SMTP_HOST",
            "smtp.example.com",
        ),
        patch(
            "src.notifications.config.notifications_settings.SMTP_USER",
            "admin@example.com",
        ),
    ):
        r = await client.post(
            f"{settings.API_V1_STR}/password-recovery",
            headers=normal_user_token_headers,
            json={"email": EMAIL_TEST_USER},
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }


async def test_recovery_password_user_not_exits(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = await client.post(
        f"{settings.API_V1_STR}/password-recovery",
        headers=normal_user_token_headers,
        json={"email": email},
    )
    assert r.status_code == 200
    assert r.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


@pytest.mark.usefixtures("normal_user_token_headers")
async def test_recovery_password_sends_the_email_to_a_registered_user(
    client: AsyncClient,
) -> None:
    with patch("src.notifications.service.send_email") as send:
        r = await client.post(
            f"{settings.API_V1_STR}/password-recovery",
            json={"email": EMAIL_TEST_USER},
        )
    assert r.status_code == 200
    send.assert_called_once()
    assert send.call_args.kwargs["email_to"] == EMAIL_TEST_USER


async def test_recovery_password_sends_nothing_for_an_unknown_email(
    client: AsyncClient,
) -> None:
    with patch("src.notifications.service.send_email") as send:
        r = await client.post(
            f"{settings.API_V1_STR}/password-recovery",
            json={"email": random_email()},
        )
    assert r.status_code == 200
    send.assert_not_called()


@pytest.mark.usefixtures("normal_user_token_headers")
async def test_recovery_password_response_does_not_reveal_a_failed_send(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    url = f"{settings.API_V1_STR}/password-recovery"
    unknown = await client.post(url, json={"email": random_email()})

    with (
        caplog.at_level("ERROR"),
        patch("src.notifications.config.notifications_settings.SMTP_HOST", None),
    ):
        registered = await client.post(url, json={"email": EMAIL_TEST_USER})

    assert (registered.status_code, registered.json()) == (
        unknown.status_code,
        unknown.json(),
    )
    assert "Failed to send the password recovery email" in caplog.text


@pytest.mark.parametrize(
    "email",
    ["first/last@example.com", "üser@example.com", "user@localhost", "a..b@x.com"],
)
async def test_recovery_password_rejects_an_address_the_contract_rejects(
    client: AsyncClient, email: str
) -> None:
    r = await client.post(
        f"{settings.API_V1_STR}/password-recovery", json={"email": email}
    )
    assert r.status_code == 422


async def test_recovery_password_rejects_a_malformed_email(client: AsyncClient) -> None:
    for payload in ({"email": "not-an-email"}, {"email": ""}, {}):
        r = await client.post(f"{settings.API_V1_STR}/password-recovery", json=payload)
        assert r.status_code == 422


async def test_reset_password(client: AsyncClient, db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    new_password = random_lower_string()

    user_create = UserCreate(
        email=email,
        full_name="Test User",
        password=password,
        is_active=True,
        is_superuser=False,
    )
    user = await create_user(session=db, user_create=user_create)
    token = generate_password_reset_token(
        email=email, hashed_password=user.hashed_password
    )
    headers = await user_authentication_headers(
        client=client, email=email, password=password
    )
    data = {"new_password": new_password, "token": token}

    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        headers=headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    await db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified


async def new_user_with_reset_token(db: AsyncSession) -> tuple[User, str]:
    user = await create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(),
            full_name="Test User",
            password=random_lower_string(),
        ),
    )
    token = generate_password_reset_token(
        email=user.email, hashed_password=user.hashed_password
    )
    return user, token


async def test_reset_password_token_works_only_once(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, token = await new_user_with_reset_token(db)
    data = {"new_password": random_lower_string(), "token": token}

    first = await client.post(f"{settings.API_V1_STR}/reset-password", json=data)
    second = await client.post(f"{settings.API_V1_STR}/reset-password", json=data)

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json() == {"detail": "Invalid token"}


async def test_reset_password_token_is_invalid_after_the_password_changes(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, token = await new_user_with_reset_token(db)
    user.hashed_password = get_password_hash(random_lower_string())
    db.add(user)
    await db.commit()

    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid token"}


async def test_reset_password_token_without_a_fingerprint_is_invalid(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, _ = await new_user_with_reset_token(db)
    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(hours=1), "sub": user.email},
        auth_settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid token"}


async def test_login_inactive_user_is_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = random_email(), random_lower_string()
    await create_user(
        session=db,
        user_create=UserCreate(
            email=email, full_name="Test User", password=password, is_active=False
        ),
    )

    r = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


async def test_reset_password_for_an_inactive_user_is_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, token = await new_user_with_reset_token(db)
    user.is_active = False
    db.add(user)
    await db.commit()

    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


async def test_reset_password_invalid_token(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": "changethis", "token": "invalid"}
    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"


async def test_login_with_bcrypt_password_upgrades_to_argon2(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    password = random_lower_string()

    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")

    user = User(
        email=email,
        full_name=random_lower_string(),
        hashed_password=bcrypt_hash,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.hashed_password.startswith("$2")

    login_data = {"username": email, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    await db.refresh(user)

    assert user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, user.hashed_password)
    assert verified
    assert updated_hash is None


async def test_login_with_argon2_password_keeps_hash(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    password = random_lower_string()

    argon2_hash = get_password_hash(password)
    assert argon2_hash.startswith("$argon2")

    user = User(
        email=email,
        full_name=random_lower_string(),
        hashed_password=argon2_hash,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    original_hash = user.hashed_password

    login_data = {"username": email, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    await db.refresh(user)

    assert user.hashed_password == original_hash
    assert user.hashed_password.startswith("$argon2")


async def test_logout_retires_every_token_of_the_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = random_email(), random_lower_string()
    await create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    first = await user_authentication_headers(
        client=client, email=email, password=password
    )
    second = await user_authentication_headers(
        client=client, email=email, password=password
    )

    r = await client.post(f"{settings.API_V1_STR}/logout", headers=first)

    me = f"{settings.API_V1_STR}/users/me"
    assert r.status_code == 204
    assert (await client.get(me, headers=first)).status_code == 401
    assert (await client.get(me, headers=second)).status_code == 401
    again = await user_authentication_headers(
        client=client, email=email, password=password
    )
    assert (await client.get(me, headers=again)).status_code == 200


async def test_logout_requires_a_session(client: AsyncClient) -> None:
    assert (await client.post(f"{settings.API_V1_STR}/logout")).status_code == 401


async def test_resetting_the_password_retires_existing_tokens(
    client: AsyncClient, db: AsyncSession
) -> None:
    email, password = random_email(), random_lower_string()
    user = await create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    headers = await user_authentication_headers(
        client=client, email=email, password=password
    )
    token = generate_password_reset_token(
        email=email, hashed_password=user.hashed_password
    )

    r = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": random_lower_string()},
    )

    assert r.status_code == 200
    me = await client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert me.status_code == 401
