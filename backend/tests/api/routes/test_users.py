import re
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.security import (
    ACCESS_AUDIENCE,
    ALGORITHM,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models import User, UserCreate
from app.utils import (
    EMAIL_CHANGE_AUDIENCE,
    SIGNUP_AUDIENCE,
    generate_email_token,
    generate_password_reset_token,
)
from tests.utils.user import (
    authentication_token_from_email,
    user_authentication_headers,
)
from tests.utils.utils import EMAIL_TEST_USER, random_email, random_lower_string


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER
    assert current_user["full_name"]


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == EMAIL_TEST_USER


def test_update_password_me(client: TestClient, db: Session) -> None:
    user, headers, password = user_with_headers(client, db)
    new_password = random_lower_string()

    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json={"current_password": password, "new_password": new_password},
    )

    assert r.status_code == 200
    db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified
    renewed = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = f"{settings.API_V1_STR}/users/me"
    assert client.get(me, headers=renewed).status_code == 200
    assert client.get(me, headers=headers).status_code == 401


def test_changing_the_password_signs_other_sessions_out(
    client: TestClient, db: Session
) -> None:
    user, first, password = user_with_headers(client, db)
    second = user_authentication_headers(
        client=client, email=user.email, password=password
    )

    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=first,
        json={"current_password": password, "new_password": random_lower_string()},
    )

    me = f"{settings.API_V1_STR}/users/me"
    assert r.status_code == 200
    assert client.get(me, headers=second).status_code == 401


def test_update_password_me_incorrect_password(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


def test_update_password_me_same_password_error(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )


def test_update_user_me_rejects_empty_full_name(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": ""},
    )
    assert r.status_code == 422


def test_update_user_me_rejects_null_fields(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    for payload in ({"full_name": None},):
        r = client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json=payload,
        )
        assert r.status_code == 422


def test_update_user_me_leaves_omitted_fields_unchanged(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    before = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    ).json()
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "Only the name"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Only the name"
    assert r.json()["email"] == before["email"]


def test_update_password_me_accepts_a_current_password_below_the_policy(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    db.add(
        User(
            email=email,
            full_name=random_lower_string(),
            hashed_password=get_password_hash("short"),
        )
    )
    db.commit()
    headers = user_authentication_headers(client=client, email=email, password="short")

    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json={"current_password": "short", "new_password": random_lower_string()},
    )
    assert r.status_code == 200


def test_update_password_me_rejects_an_empty_current_password(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json={"current_password": "", "new_password": random_lower_string()},
    )
    assert r.status_code == 422


def test_invalid_token_is_unauthorized(client: TestClient) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json() == {"detail": "Could not validate credentials"}


def test_token_for_a_user_without_an_account_is_unauthorized(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.get_user_by_email(session=db, email=email)
    assert user
    db.delete(user)
    db.commit()
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json() == {"detail": "Could not validate credentials"}


def test_inactive_user_is_forbidden(client: TestClient, db: Session) -> None:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.get_user_by_email(session=db, email=email)
    assert user
    user.is_active = False
    db.add(user)
    db.commit()
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 403
    assert r.json() == {"detail": "Inactive user"}


def test_missing_token_is_unauthorized(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 401


def delete_account(
    client: TestClient, headers: dict[str, str], password: str
) -> httpx.Response:
    return client.request(
        "DELETE",
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json={"current_password": password},
    )


def test_delete_user_me(client: TestClient, db: Session) -> None:
    user, headers, password = user_with_headers(client, db)
    user_id = user.id

    r = delete_account(client, headers, password)

    assert r.status_code == 204
    assert r.content == b""
    assert db.exec(select(User).where(User.id == user_id)).first() is None


def test_delete_user_me_requires_the_current_password(
    client: TestClient, db: Session
) -> None:
    user, headers, _ = user_with_headers(client, db)
    email = user.email

    r = delete_account(client, headers, "not-the-password")

    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect password"}
    assert crud.get_user_by_email(session=db, email=email)


def test_delete_user_me_without_a_body_is_rejected(
    client: TestClient, db: Session
) -> None:
    _, headers, _ = user_with_headers(client, db)

    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert r.status_code == 422


def test_delete_user_me_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = delete_account(
        client, superuser_token_headers, settings.FIRST_SUPERUSER_PASSWORD
    )
    assert r.status_code == 403
    response = r.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


def emailed_token(send: MagicMock) -> str:
    for call in send.call_args_list:
        match = re.search(r"\?token=([\w.-]+)", call.kwargs["html_content"])
        if match:
            return match.group(1)
    raise AssertionError("no email carried a link")


def sent_to(send: MagicMock, address: str) -> list[str]:
    return [
        call.kwargs["html_content"]
        for call in send.call_args_list
        if call.kwargs["email_to"] == address
    ]


def signup_token(email: str) -> str:
    return generate_email_token(
        audience=SIGNUP_AUDIENCE,
        claims={"sub": email, "name": "New User"},
        expires_in=timedelta(hours=1),
    )


def user_with_headers(
    client: TestClient, db: Session
) -> tuple[User, dict[str, str], str]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(), full_name=random_lower_string(), password=password
        ),
    )
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    return user, headers, password


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "Updated Name"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"
    assert r.json()["email"] == EMAIL_TEST_USER

    user_db = crud.get_user_by_email(session=db, email=EMAIL_TEST_USER)
    assert user_db
    assert user_db.full_name == "Updated Name"


def test_update_user_me_cannot_change_the_email(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": random_email()},
    )
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL_TEST_USER


def test_signup_emails_a_link_to_a_new_address(client: TestClient, db: Session) -> None:
    email = random_email()
    with patch("app.utils.send_email") as send:
        r = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": email, "full_name": "New User"},
        )
    assert r.status_code == 200
    send.assert_called_once()
    assert send.call_args.kwargs["email_to"] == email
    assert "/signup/complete?token=" in send.call_args.kwargs["html_content"]
    assert crud.get_user_by_email(session=db, email=email) is None


def test_signup_sends_nothing_to_a_registered_address(client: TestClient) -> None:
    with patch("app.utils.send_email") as send:
        r = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": settings.FIRST_SUPERUSER, "full_name": "New User"},
        )
    assert r.status_code == 200
    send.assert_not_called()


def test_signup_answers_the_same_for_every_address(client: TestClient) -> None:
    url = f"{settings.API_V1_STR}/users/signup"
    with patch("app.utils.send_email"):
        new = client.post(url, json={"email": random_email(), "full_name": "A"})
        registered = client.post(
            url, json={"email": settings.FIRST_SUPERUSER, "full_name": "A"}
        )
    assert (new.status_code, new.json()) == (registered.status_code, registered.json())


def test_signup_response_does_not_reveal_a_failed_send(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with (
        caplog.at_level("ERROR"),
        patch("app.core.config.settings.SMTP_HOST", None),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": random_email(), "full_name": "New User"},
        )
    assert r.status_code == 200
    assert "Failed to send the confirmation email" in caplog.text


def test_signup_requires_an_email_and_a_full_name(client: TestClient) -> None:
    for payload in (
        {"email": random_email()},
        {"email": random_email(), "full_name": ""},
        {"full_name": "New User"},
    ):
        r = client.post(f"{settings.API_V1_STR}/users/signup", json=payload)
        assert r.status_code == 422


def test_complete_signup_creates_a_user_who_can_log_in(client: TestClient) -> None:
    email = random_email()
    password = random_lower_string()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(email), "new_password": password},
    )
    assert r.status_code == 201
    assert r.json()["email"] == email
    assert r.json()["full_name"] == "New User"

    login = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200


def test_a_signup_link_works_once(client: TestClient) -> None:
    body = {
        "token": signup_token(random_email()),
        "new_password": random_lower_string(),
    }
    url = f"{settings.API_V1_STR}/users/signup/complete"

    assert client.post(url, json=body).status_code == 201
    again = client.post(url, json=body)

    assert again.status_code == 400
    assert again.json()["detail"] == "Invalid token"


def test_complete_signup_rejects_an_expired_token(client: TestClient) -> None:
    token = generate_email_token(
        audience=SIGNUP_AUDIENCE,
        claims={"sub": random_email(), "name": "New User"},
        expires_in=timedelta(seconds=-1),
    )
    r = client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": token, "new_password": random_lower_string()},
    )
    assert r.status_code == 400


def test_complete_signup_rejects_a_weak_password(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(random_email()), "new_password": "short"},
    )
    assert r.status_code == 422


def test_complete_signup_rejects_tokens_made_for_another_purpose(
    client: TestClient,
) -> None:
    email = random_email()
    tokens = [
        generate_password_reset_token(email=email, hashed_password="hash"),
        generate_email_token(
            audience=EMAIL_CHANGE_AUDIENCE,
            claims={"sub": email, "name": "New User"},
            expires_in=timedelta(hours=1),
        ),
        create_access_token(email, expires_delta=timedelta(minutes=5), token_version=0),
    ]
    for token in tokens:
        r = client.post(
            f"{settings.API_V1_STR}/users/signup/complete",
            json={"token": token, "new_password": random_lower_string()},
        )
        assert r.status_code == 400


def test_a_signup_token_cannot_reset_a_password_or_authenticate(
    client: TestClient,
) -> None:
    token = signup_token(settings.FIRST_SUPERUSER)

    reset = client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": random_lower_string()},
    )
    me = client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert reset.status_code == 400
    assert me.status_code == 401


def request_email_change(
    client: TestClient, headers: dict[str, str], email: str, password: str
) -> httpx.Response:
    return client.post(
        f"{settings.API_V1_STR}/users/me/email",
        headers=headers,
        json={"email": email, "current_password": password},
    )


def test_email_change_request_requires_authentication(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/me/email",
        json={"email": random_email(), "current_password": "x"},
    )
    assert r.status_code == 401


def test_email_change_emails_a_link_to_the_new_address(
    client: TestClient, db: Session
) -> None:
    user, headers, password = user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("app.utils.send_email") as send:
        r = request_email_change(client, headers, new_email, password)
    assert r.status_code == 200
    (to_new,) = sent_to(send, new_email)
    assert "/confirm-email?token=" in to_new
    db.refresh(user)
    assert user.email == old_email


def test_email_change_requires_the_current_password(
    client: TestClient, db: Session
) -> None:
    _, headers, _ = user_with_headers(client, db)
    with patch("app.utils.send_email") as send:
        r = request_email_change(client, headers, random_email(), "not-the-password")
    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect password"}
    send.assert_not_called()


def test_email_change_request_tells_the_current_address(
    client: TestClient, db: Session
) -> None:
    user, headers, password = user_with_headers(client, db)
    new_email = random_email()
    with patch("app.utils.send_email") as send:
        request_email_change(client, headers, new_email, password)
    (notice,) = sent_to(send, user.email)
    assert new_email in notice
    assert "?token=" not in notice


def test_email_change_answers_the_same_for_a_taken_address(
    client: TestClient, db: Session
) -> None:
    _, headers, password = user_with_headers(client, db)
    free_address = random_email()
    with patch("app.utils.send_email") as send:
        taken = request_email_change(
            client, headers, settings.FIRST_SUPERUSER, password
        )
        free = request_email_change(client, headers, free_address, password)
    assert (taken.status_code, taken.json()) == (free.status_code, free.json())
    assert sent_to(send, settings.FIRST_SUPERUSER) == []
    assert len(sent_to(send, free_address)) == 1


def test_confirming_an_email_change_applies_it(client: TestClient, db: Session) -> None:
    user, headers, password = user_with_headers(client, db)
    new_email = random_email()
    with patch("app.utils.send_email") as send:
        request_email_change(client, headers, new_email, password)

    r = client.post(
        f"{settings.API_V1_STR}/users/confirm-email",
        json={"token": emailed_token(send)},
    )

    assert r.status_code == 200
    renewed = user_authentication_headers(
        client=client, email=new_email, password=password
    )
    me = client.get(f"{settings.API_V1_STR}/users/me", headers=renewed)
    assert me.json()["email"] == new_email


def test_applying_an_email_change_signs_every_session_out_and_tells_the_old_address(
    client: TestClient, db: Session
) -> None:
    user, headers, password = user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("app.utils.send_email") as send:
        request_email_change(client, headers, new_email, password)
        client.post(
            f"{settings.API_V1_STR}/users/confirm-email",
            json={"token": emailed_token(send)},
        )

    assert (
        client.get(f"{settings.API_V1_STR}/users/me", headers=headers).status_code
        == 401
    )
    notices = sent_to(send, old_email)
    assert len(notices) == 2
    assert new_email in notices[-1]


def test_an_email_change_link_works_once(client: TestClient, db: Session) -> None:
    _, headers, password = user_with_headers(client, db)
    with patch("app.utils.send_email") as send:
        request_email_change(client, headers, random_email(), password)
    body = {"token": emailed_token(send)}
    url = f"{settings.API_V1_STR}/users/confirm-email"

    assert client.post(url, json=body).status_code == 200
    assert client.post(url, json=body).status_code == 400


def test_an_email_change_fails_when_the_address_was_taken_meanwhile(
    client: TestClient, db: Session
) -> None:
    user, headers, password = user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("app.utils.send_email") as send:
        request_email_change(client, headers, new_email, password)
    crud.create_user(
        session=db,
        user_create=UserCreate(
            email=new_email, full_name=random_lower_string(), password="password123"
        ),
    )

    r = client.post(
        f"{settings.API_V1_STR}/users/confirm-email",
        json={"token": emailed_token(send)},
    )

    assert r.status_code == 400
    db.refresh(user)
    assert user.email == old_email


def test_confirm_email_change_rejects_tokens_made_for_another_purpose(
    client: TestClient,
) -> None:
    email = random_email()
    for token in (
        signup_token(email),
        generate_password_reset_token(email=email, hashed_password="hash"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/users/confirm-email", json={"token": token}
        )
        assert r.status_code == 400


def test_an_access_token_without_a_version_is_rejected(
    client: TestClient, db: Session
) -> None:
    user, _, _ = user_with_headers(client, db)
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(user.id),
            "aud": ACCESS_AUDIENCE,
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


def test_a_token_without_an_audience_is_rejected(
    client: TestClient, db: Session
) -> None:
    user, _, _ = user_with_headers(client, db)
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(user.id),
            "ver": user.token_version,
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


def test_a_password_reset_token_cannot_authenticate(client: TestClient) -> None:
    token = generate_password_reset_token(
        email=settings.FIRST_SUPERUSER, hashed_password="hash"
    )

    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


def test_emails_are_stored_and_matched_in_lowercase(client: TestClient) -> None:
    address = random_email()
    mixed = address.upper()
    password = random_lower_string()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(mixed), "new_password": password},
    )
    assert r.status_code == 201
    assert r.json()["email"] == address

    login = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": mixed, "password": password},
    )
    assert login.status_code == 200
    again = client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(address), "new_password": password},
    )
    assert again.status_code == 400
    with patch("app.utils.send_email") as send:
        client.post(f"{settings.API_V1_STR}/password-recovery", json={"email": mixed})
    assert len(sent_to(send, address)) == 1


def test_completing_a_signup_that_loses_the_race_answers_400(
    client: TestClient, db: Session
) -> None:
    taken, _, _ = user_with_headers(client, db)

    with patch("app.api.routes.users.crud.get_user_by_email", return_value=None):
        r = client.post(
            f"{settings.API_V1_STR}/users/signup/complete",
            json={
                "token": signup_token(taken.email),
                "new_password": random_lower_string(),
            },
        )

    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"


def test_confirming_an_email_change_that_loses_the_race_answers_400(
    client: TestClient, db: Session
) -> None:
    user, _, _ = user_with_headers(client, db)
    taken, _, _ = user_with_headers(client, db)
    original_email, original_version = user.email, user.token_version
    token = generate_email_token(
        audience=EMAIL_CHANGE_AUDIENCE,
        claims={"sub": str(user.id), "email": taken.email, "from": user.email},
        expires_in=timedelta(hours=1),
    )

    with patch("app.api.routes.users.crud.get_user_by_email", return_value=None):
        r = client.post(
            f"{settings.API_V1_STR}/users/confirm-email", json={"token": token}
        )

    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"
    db.refresh(user)
    assert (user.email, user.token_version) == (original_email, original_version)
