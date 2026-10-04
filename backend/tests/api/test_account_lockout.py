from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session

from app import crud
from app.core import throttle
from app.core.config import settings
from app.models import UserCreate, get_datetime_utc
from app.utils import generate_password_reset_token
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

LOGIN = f"{settings.API_V1_STR}/login/access-token"
USERS = f"{settings.API_V1_STR}/users"


def make_user(db: Session) -> tuple[str, str]:
    email, password = random_email(), random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(email=email, full_name="Test User", password=password),
    )
    return email, password


def log_in(client: TestClient, email: str, password: str) -> Response:
    response: Response = client.post(
        LOGIN, data={"username": email, "password": password}
    )
    return response


def fail_login(client: TestClient, email: str, times: int) -> None:
    for _ in range(times):
        assert log_in(client, email, "wrong-password").status_code == 400


def advance(monkeypatch: pytest.MonkeyPatch, minutes: int) -> None:
    now = get_datetime_utc()
    monkeypatch.setattr(
        throttle, "get_datetime_utc", lambda: now + timedelta(minutes=minutes)
    )


def test_account_locks_after_repeated_failures_even_for_the_right_password(
    client: TestClient, db: Session
) -> None:
    email, password = make_user(db)
    fail_login(client, email, settings.AUTH_MAX_FAILURES)

    response = log_in(client, email, password)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) <= settings.AUTH_LOCK_MINUTES * 60
    assert "Try again in 15 minutes" in response.json()["detail"]


def test_an_unknown_email_is_locked_exactly_like_a_known_one(
    client: TestClient, db: Session
) -> None:
    known, password = make_user(db)
    unknown = random_email()
    fail_login(client, known, settings.AUTH_MAX_FAILURES)
    fail_login(client, unknown, settings.AUTH_MAX_FAILURES)

    locked_known = log_in(client, known, password)
    locked_unknown = log_in(client, unknown, "anything")

    assert locked_known.status_code == locked_unknown.status_code == 429
    assert locked_known.json() == locked_unknown.json()


def test_a_failure_on_one_account_does_not_lock_another(
    client: TestClient, db: Session
) -> None:
    _, _ = make_user(db)
    other, other_password = make_user(db)
    fail_login(client, random_email(), settings.AUTH_MAX_FAILURES)

    assert log_in(client, other, other_password).status_code == 200


def test_a_successful_login_resets_the_count(client: TestClient, db: Session) -> None:
    email, password = make_user(db)
    fail_login(client, email, settings.AUTH_MAX_FAILURES - 1)
    assert log_in(client, email, password).status_code == 200

    fail_login(client, email, settings.AUTH_MAX_FAILURES - 1)

    assert log_in(client, email, password).status_code == 200


def test_the_lock_expires(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    email, password = make_user(db)
    fail_login(client, email, settings.AUTH_MAX_FAILURES)
    assert log_in(client, email, password).status_code == 429

    advance(monkeypatch, settings.AUTH_LOCK_MINUTES + 1)

    assert log_in(client, email, password).status_code == 200


def test_old_failures_stop_counting(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    email, password = make_user(db)
    fail_login(client, email, settings.AUTH_MAX_FAILURES - 1)

    advance(monkeypatch, settings.AUTH_LOCK_MINUTES + 1)
    fail_login(client, email, settings.AUTH_MAX_FAILURES - 1)

    assert log_in(client, email, password).status_code == 200


def test_wrong_current_passwords_lock_every_password_check_and_login(
    client: TestClient, db: Session
) -> None:
    email, password = make_user(db)
    headers = user_authentication_headers(client=client, email=email, password=password)
    for _ in range(settings.AUTH_MAX_FAILURES):
        response = client.patch(
            f"{USERS}/me/password",
            headers=headers,
            json={"current_password": "wrong-password", "new_password": "new-password"},
        )
        assert response.status_code == 400

    right = {"current_password": password, "new_password": "new-password"}
    assert (
        client.patch(f"{USERS}/me/password", headers=headers, json=right).status_code
        == 429
    )
    assert (
        client.post(
            f"{USERS}/me/email",
            headers=headers,
            json={"email": random_email(), "current_password": password},
        ).status_code
        == 429
    )
    assert (
        client.request(
            "DELETE",
            f"{USERS}/me",
            headers=headers,
            json={"current_password": password},
        ).status_code
        == 429
    )
    assert log_in(client, email, password).status_code == 429


def test_resetting_the_password_unlocks_the_account(
    client: TestClient, db: Session
) -> None:
    email, password = make_user(db)
    fail_login(client, email, settings.AUTH_MAX_FAILURES)
    user = crud.get_user_by_email(session=db, email=email)
    assert user
    token = generate_password_reset_token(email, user.hashed_password)

    reset = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": "brand-new-password"},
    )

    assert reset.status_code == 200
    assert log_in(client, email, "brand-new-password").status_code == 200
