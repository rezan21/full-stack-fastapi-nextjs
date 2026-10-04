from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session

from app.core.config import settings
from app.core.security import ALGORITHM, get_password_hash, verify_password
from app.crud import create_user
from app.models import User, UserCreate
from app.utils import generate_password_reset_token
from tests.utils.user import user_authentication_headers
from tests.utils.utils import EMAIL_TEST_USER, random_email, random_lower_string


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]
    assert tokens["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_recovery_password(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery",
            headers=normal_user_token_headers,
            json={"email": EMAIL_TEST_USER},
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery",
        headers=normal_user_token_headers,
        json={"email": email},
    )
    assert r.status_code == 200
    assert r.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


@pytest.mark.usefixtures("normal_user_token_headers")
def test_recovery_password_sends_the_email_to_a_registered_user(
    client: TestClient,
) -> None:
    with patch("app.utils.send_email") as send:
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery",
            json={"email": EMAIL_TEST_USER},
        )
    assert r.status_code == 200
    send.assert_called_once()
    assert send.call_args.kwargs["email_to"] == EMAIL_TEST_USER


def test_recovery_password_sends_nothing_for_an_unknown_email(
    client: TestClient,
) -> None:
    with patch("app.utils.send_email") as send:
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery",
            json={"email": random_email()},
        )
    assert r.status_code == 200
    send.assert_not_called()


@pytest.mark.usefixtures("normal_user_token_headers")
def test_recovery_password_response_does_not_reveal_a_failed_send(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    url = f"{settings.API_V1_STR}/password-recovery"
    unknown = client.post(url, json={"email": random_email()})

    with (
        caplog.at_level("ERROR"),
        patch("app.core.config.settings.SMTP_HOST", None),
    ):
        registered = client.post(url, json={"email": EMAIL_TEST_USER})

    assert (registered.status_code, registered.json()) == (
        unknown.status_code,
        unknown.json(),
    )
    assert "Failed to send the password recovery email" in caplog.text


def test_recovery_password_accepts_a_slash_in_the_address(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery",
        json={"email": "first/last@example.com"},
    )
    assert r.status_code == 200


def test_recovery_password_rejects_a_malformed_email(client: TestClient) -> None:
    for payload in ({"email": "not-an-email"}, {"email": ""}, {}):
        r = client.post(f"{settings.API_V1_STR}/password-recovery", json=payload)
        assert r.status_code == 422


def test_reset_password(client: TestClient, db: Session) -> None:
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
    user = create_user(session=db, user_create=user_create)
    token = generate_password_reset_token(
        email=email, hashed_password=user.hashed_password
    )
    headers = user_authentication_headers(client=client, email=email, password=password)
    data = {"new_password": new_password, "token": token}

    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        headers=headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified


def new_user_with_reset_token(db: Session) -> tuple[User, str]:
    user = create_user(
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


def test_reset_password_token_works_only_once(client: TestClient, db: Session) -> None:
    _, token = new_user_with_reset_token(db)
    data = {"new_password": random_lower_string(), "token": token}

    first = client.post(f"{settings.API_V1_STR}/reset-password", json=data)
    second = client.post(f"{settings.API_V1_STR}/reset-password", json=data)

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json() == {"detail": "Invalid token"}


def test_reset_password_token_is_invalid_after_the_password_changes(
    client: TestClient, db: Session
) -> None:
    user, token = new_user_with_reset_token(db)
    user.hashed_password = get_password_hash(random_lower_string())
    db.add(user)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid token"}


def test_reset_password_token_without_a_fingerprint_is_invalid(
    client: TestClient, db: Session
) -> None:
    user, _ = new_user_with_reset_token(db)
    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(hours=1), "sub": user.email},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid token"}


def test_login_inactive_user_is_rejected(client: TestClient, db: Session) -> None:
    email, password = random_email(), random_lower_string()
    create_user(
        session=db,
        user_create=UserCreate(
            email=email, full_name="Test User", password=password, is_active=False
        ),
    )

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


def test_reset_password_for_an_inactive_user_is_rejected(
    client: TestClient, db: Session
) -> None:
    user, token = new_user_with_reset_token(db)
    user.is_active = False
    db.add(user)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"new_password": random_lower_string(), "token": token},
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Inactive user"}


def test_reset_password_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"


def test_login_with_bcrypt_password_upgrades_to_argon2(
    client: TestClient, db: Session
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
    db.commit()
    db.refresh(user)

    assert user.hashed_password.startswith("$2")

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    assert user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, user.hashed_password)
    assert verified
    assert updated_hash is None


def test_login_with_argon2_password_keeps_hash(client: TestClient, db: Session) -> None:
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
    db.commit()
    db.refresh(user)

    original_hash = user.hashed_password

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    assert user.hashed_password == original_hash
    assert user.hashed_password.startswith("$argon2")


def test_logout_retires_every_token_of_the_user(
    client: TestClient, db: Session
) -> None:
    email, password = random_email(), random_lower_string()
    create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    first = user_authentication_headers(client=client, email=email, password=password)
    second = user_authentication_headers(client=client, email=email, password=password)

    r = client.post(f"{settings.API_V1_STR}/logout", headers=first)

    me = f"{settings.API_V1_STR}/users/me"
    assert r.status_code == 204
    assert client.get(me, headers=first).status_code == 401
    assert client.get(me, headers=second).status_code == 401
    again = user_authentication_headers(client=client, email=email, password=password)
    assert client.get(me, headers=again).status_code == 200


def test_logout_requires_a_session(client: TestClient) -> None:
    assert client.post(f"{settings.API_V1_STR}/logout").status_code == 401


def test_resetting_the_password_retires_existing_tokens(
    client: TestClient, db: Session
) -> None:
    email, password = random_email(), random_lower_string()
    user = create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    headers = user_authentication_headers(client=client, email=email, password=password)
    token = generate_password_reset_token(
        email=email, hashed_password=user.hashed_password
    )

    r = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": random_lower_string()},
    )

    assert r.status_code == 200
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert me.status_code == 401
