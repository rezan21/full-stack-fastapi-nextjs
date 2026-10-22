import re
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import httpx
import jwt
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.config import auth_settings
from src.auth.constants import ACCESS_AUDIENCE, ALGORITHM
from src.auth.utils import (
    create_access_token,
    generate_email_token,
    generate_password_reset_token,
    get_password_hash,
    verify_password,
)
from src.config import settings
from src.users import service as users_service
from src.users.config import users_settings
from src.users.constants import EMAIL_CHANGE_AUDIENCE, SIGNUP_AUDIENCE
from src.users.models import User
from src.users.schemas import UserCreate
from tests.utils.user import (
    authentication_token_from_email,
    user_authentication_headers,
)
from tests.utils.utils import EMAIL_TEST_USER, random_email, random_lower_string


async def test_get_users_superuser_me(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers
    )
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == users_settings.FIRST_SUPERUSER
    assert current_user["full_name"]


async def test_get_users_normal_user_me(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    )
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == EMAIL_TEST_USER


async def test_update_password_me(client: AsyncClient, db: AsyncSession) -> None:
    user, headers, password = await user_with_headers(client, db)
    new_password = random_lower_string()

    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json={"current_password": password, "new_password": new_password},
    )

    assert r.status_code == 200
    await db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified
    renewed = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = f"{settings.API_V1_STR}/users/me"
    assert (await client.get(me, headers=renewed)).status_code == 200
    assert (await client.get(me, headers=headers)).status_code == 401


async def test_changing_the_password_signs_other_sessions_out(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, first, password = await user_with_headers(client, db)
    second = await user_authentication_headers(
        client=client, email=user.email, password=password
    )

    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=first,
        json={"current_password": password, "new_password": random_lower_string()},
    )

    me = f"{settings.API_V1_STR}/users/me"
    assert r.status_code == 200
    assert (await client.get(me, headers=second)).status_code == 401


async def test_update_password_me_incorrect_password(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


async def test_update_password_me_same_password_error(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "current_password": users_settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": users_settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )


async def test_update_user_me_rejects_empty_full_name(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": ""},
    )
    assert r.status_code == 422


async def test_update_user_me_rejects_null_fields(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    for payload in ({"full_name": None},):
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json=payload,
        )
        assert r.status_code == 422


async def test_update_user_me_leaves_omitted_fields_unchanged(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    before = (
        await client.get(
            f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
        )
    ).json()
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "Only the name"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Only the name"
    assert r.json()["email"] == before["email"]


async def test_update_password_me_accepts_a_current_password_below_the_policy(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    db.add(
        User(
            email=email,
            full_name=random_lower_string(),
            hashed_password=get_password_hash("short"),
        )
    )
    await db.commit()
    headers = await user_authentication_headers(
        client=client, email=email, password="short"
    )

    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json={"current_password": "short", "new_password": random_lower_string()},
    )
    assert r.status_code == 200


async def test_update_password_me_rejects_an_empty_current_password(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json={"current_password": "", "new_password": random_lower_string()},
    )
    assert r.status_code == 422


async def test_invalid_token_is_unauthorized(client: AsyncClient) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json() == {"detail": "Could not validate credentials"}


async def test_token_for_a_user_without_an_account_is_unauthorized(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    headers = await authentication_token_from_email(client=client, email=email, db=db)
    user = await users_service.get_user_by_email(session=db, email=email)
    assert user
    await db.delete(user)
    await db.commit()
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json() == {"detail": "Could not validate credentials"}


async def test_inactive_user_is_forbidden(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    headers = await authentication_token_from_email(client=client, email=email, db=db)
    user = await users_service.get_user_by_email(session=db, email=email)
    assert user
    user.is_active = False
    db.add(user)
    await db.commit()
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 403
    assert r.json() == {"detail": "Inactive user"}


async def test_missing_token_is_unauthorized(client: AsyncClient) -> None:
    r = await client.get(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 401


async def delete_account(
    client: AsyncClient, headers: dict[str, str], password: str
) -> httpx.Response:
    return await client.request(
        "DELETE",
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json={"current_password": password},
    )


async def test_delete_user_me(client: AsyncClient, db: AsyncSession) -> None:
    user, headers, password = await user_with_headers(client, db)
    user_id = user.id

    r = await delete_account(client, headers, password)

    assert r.status_code == 204
    assert r.content == b""
    assert (await db.exec(select(User).where(User.id == user_id))).first() is None


async def test_delete_user_me_requires_the_current_password(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, _ = await user_with_headers(client, db)
    email = user.email

    r = await delete_account(client, headers, "not-the-password")

    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect password"}
    assert await users_service.get_user_by_email(session=db, email=email)


async def test_delete_user_me_without_a_body_is_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, headers, _ = await user_with_headers(client, db)

    r = await client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert r.status_code == 422


async def test_delete_user_me_as_superuser(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await delete_account(
        client, superuser_token_headers, users_settings.FIRST_SUPERUSER_PASSWORD
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


async def user_with_headers(
    client: AsyncClient, db: AsyncSession
) -> tuple[User, dict[str, str], str]:
    password = random_lower_string()
    user = await users_service.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(), full_name=random_lower_string(), password=password
        ),
    )
    headers = await user_authentication_headers(
        client=client, email=user.email, password=password
    )
    return user, headers, password


async def test_update_user_me(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "Updated Name"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"
    assert r.json()["email"] == EMAIL_TEST_USER

    user_db = await users_service.get_user_by_email(session=db, email=EMAIL_TEST_USER)
    assert user_db
    assert user_db.full_name == "Updated Name"


async def test_update_user_me_cannot_change_the_email(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": random_email()},
    )
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL_TEST_USER


async def test_signup_emails_a_link_to_a_new_address(
    client: AsyncClient, db: AsyncSession
) -> None:
    email = random_email()
    with patch("src.notifications.service.send_email") as send:
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": email, "full_name": "New User"},
        )
    assert r.status_code == 200
    send.assert_called_once()
    assert send.call_args.kwargs["email_to"] == email
    assert "/signup/complete?token=" in send.call_args.kwargs["html_content"]
    assert await users_service.get_user_by_email(session=db, email=email) is None


async def test_signup_sends_nothing_to_a_registered_address(
    client: AsyncClient,
) -> None:
    with patch("src.notifications.service.send_email") as send:
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": users_settings.FIRST_SUPERUSER, "full_name": "New User"},
        )
    assert r.status_code == 200
    send.assert_not_called()


async def test_signup_answers_the_same_for_every_address(client: AsyncClient) -> None:
    url = f"{settings.API_V1_STR}/users/signup"
    with patch("src.notifications.service.send_email"):
        new = await client.post(url, json={"email": random_email(), "full_name": "A"})
        registered = await client.post(
            url, json={"email": users_settings.FIRST_SUPERUSER, "full_name": "A"}
        )
    assert (new.status_code, new.json()) == (registered.status_code, registered.json())


async def test_signup_response_does_not_reveal_a_failed_send(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with (
        caplog.at_level("ERROR"),
        patch("src.notifications.config.notifications_settings.SMTP_HOST", None),
    ):
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup",
            json={"email": random_email(), "full_name": "New User"},
        )
    assert r.status_code == 200
    assert "Failed to send the confirmation email" in caplog.text


async def test_signup_requires_an_email_and_a_full_name(client: AsyncClient) -> None:
    for payload in (
        {"email": random_email()},
        {"email": random_email(), "full_name": ""},
        {"full_name": "New User"},
    ):
        r = await client.post(f"{settings.API_V1_STR}/users/signup", json=payload)
        assert r.status_code == 422


async def test_complete_signup_creates_a_user_who_can_log_in(
    client: AsyncClient,
) -> None:
    email = random_email()
    password = random_lower_string()
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(email), "new_password": password},
    )
    assert r.status_code == 201
    assert r.json()["email"] == email
    assert r.json()["full_name"] == "New User"

    login = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200


async def test_a_signup_link_works_once(client: AsyncClient) -> None:
    body = {
        "token": signup_token(random_email()),
        "new_password": random_lower_string(),
    }
    url = f"{settings.API_V1_STR}/users/signup/complete"

    assert (await client.post(url, json=body)).status_code == 201
    again = await client.post(url, json=body)

    assert again.status_code == 400
    assert again.json()["detail"] == "Invalid token"


async def test_complete_signup_rejects_an_expired_token(client: AsyncClient) -> None:
    token = generate_email_token(
        audience=SIGNUP_AUDIENCE,
        claims={"sub": random_email(), "name": "New User"},
        expires_in=timedelta(seconds=-1),
    )
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": token, "new_password": random_lower_string()},
    )
    assert r.status_code == 400


async def test_complete_signup_rejects_a_weak_password(client: AsyncClient) -> None:
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(random_email()), "new_password": "short"},
    )
    assert r.status_code == 422


async def test_complete_signup_rejects_tokens_made_for_another_purpose(
    client: AsyncClient,
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
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup/complete",
            json={"token": token, "new_password": random_lower_string()},
        )
        assert r.status_code == 400


async def test_a_signup_token_cannot_reset_a_password_or_authenticate(
    client: AsyncClient,
) -> None:
    token = signup_token(users_settings.FIRST_SUPERUSER)

    reset = await client.post(
        f"{settings.API_V1_STR}/reset-password",
        json={"token": token, "new_password": random_lower_string()},
    )
    me = await client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert reset.status_code == 400
    assert me.status_code == 401


async def request_email_change(
    client: AsyncClient, headers: dict[str, str], email: str, password: str
) -> httpx.Response:
    return await client.post(
        f"{settings.API_V1_STR}/users/me/email",
        headers=headers,
        json={"email": email, "current_password": password},
    )


async def test_email_change_request_requires_authentication(
    client: AsyncClient,
) -> None:
    r = await client.post(
        f"{settings.API_V1_STR}/users/me/email",
        json={"email": random_email(), "current_password": "x"},
    )
    assert r.status_code == 401


async def test_email_change_emails_a_link_to_the_new_address(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, password = await user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("src.notifications.service.send_email") as send:
        r = await request_email_change(client, headers, new_email, password)
    assert r.status_code == 200
    (to_new,) = sent_to(send, new_email)
    assert "/confirm-email?token=" in to_new
    await db.refresh(user)
    assert user.email == old_email


async def test_email_change_requires_the_current_password(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, headers, _ = await user_with_headers(client, db)
    with patch("src.notifications.service.send_email") as send:
        r = await request_email_change(
            client, headers, random_email(), "not-the-password"
        )
    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect password"}
    send.assert_not_called()


async def test_email_change_request_tells_the_current_address(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, password = await user_with_headers(client, db)
    new_email = random_email()
    with patch("src.notifications.service.send_email") as send:
        await request_email_change(client, headers, new_email, password)
    (notice,) = sent_to(send, user.email)
    assert new_email in notice
    assert "?token=" not in notice


async def test_email_change_answers_the_same_for_a_taken_address(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, headers, password = await user_with_headers(client, db)
    free_address = random_email()
    with patch("src.notifications.service.send_email") as send:
        taken = await request_email_change(
            client, headers, users_settings.FIRST_SUPERUSER, password
        )
        free = await request_email_change(client, headers, free_address, password)
    assert (taken.status_code, taken.json()) == (free.status_code, free.json())
    assert sent_to(send, users_settings.FIRST_SUPERUSER) == []
    assert len(sent_to(send, free_address)) == 1


async def test_confirming_an_email_change_applies_it(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, password = await user_with_headers(client, db)
    new_email = random_email()
    with patch("src.notifications.service.send_email") as send:
        await request_email_change(client, headers, new_email, password)

    r = await client.post(
        f"{settings.API_V1_STR}/users/confirm-email",
        json={"token": emailed_token(send)},
    )

    assert r.status_code == 200
    renewed = await user_authentication_headers(
        client=client, email=new_email, password=password
    )
    me = await client.get(f"{settings.API_V1_STR}/users/me", headers=renewed)
    assert me.json()["email"] == new_email


async def test_applying_an_email_change_signs_every_session_out_and_tells_the_old_address(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, password = await user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("src.notifications.service.send_email") as send:
        await request_email_change(client, headers, new_email, password)
        await client.post(
            f"{settings.API_V1_STR}/users/confirm-email",
            json={"token": emailed_token(send)},
        )

    assert (
        await client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    ).status_code == 401
    notices = sent_to(send, old_email)
    assert len(notices) == 2
    assert new_email in notices[-1]


async def test_an_email_change_link_works_once(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, headers, password = await user_with_headers(client, db)
    with patch("src.notifications.service.send_email") as send:
        await request_email_change(client, headers, random_email(), password)
    body = {"token": emailed_token(send)}
    url = f"{settings.API_V1_STR}/users/confirm-email"

    assert (await client.post(url, json=body)).status_code == 200
    assert (await client.post(url, json=body)).status_code == 400


async def test_an_email_change_fails_when_the_address_was_taken_meanwhile(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, headers, password = await user_with_headers(client, db)
    old_email = user.email
    new_email = random_email()
    with patch("src.notifications.service.send_email") as send:
        await request_email_change(client, headers, new_email, password)
    await users_service.create_user(
        session=db,
        user_create=UserCreate(
            email=new_email, full_name=random_lower_string(), password="password123"
        ),
    )

    r = await client.post(
        f"{settings.API_V1_STR}/users/confirm-email",
        json={"token": emailed_token(send)},
    )

    assert r.status_code == 400
    await db.refresh(user)
    assert user.email == old_email


async def test_confirm_email_change_rejects_tokens_made_for_another_purpose(
    client: AsyncClient,
) -> None:
    email = random_email()
    for token in (
        signup_token(email),
        generate_password_reset_token(email=email, hashed_password="hash"),
    ):
        r = await client.post(
            f"{settings.API_V1_STR}/users/confirm-email", json={"token": token}
        )
        assert r.status_code == 400


async def test_an_access_token_without_a_version_is_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, _, _ = await user_with_headers(client, db)
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(user.id),
            "aud": ACCESS_AUDIENCE,
        },
        auth_settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


async def test_a_token_without_an_audience_is_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, _, _ = await user_with_headers(client, db)
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(user.id),
            "ver": user.token_version,
        },
        auth_settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


async def test_a_password_reset_token_cannot_authenticate(client: AsyncClient) -> None:
    token = generate_password_reset_token(
        email=users_settings.FIRST_SUPERUSER, hashed_password="hash"
    )

    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401


async def test_emails_are_stored_and_matched_in_lowercase(client: AsyncClient) -> None:
    address = random_email()
    mixed = address.upper()
    password = random_lower_string()
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(mixed), "new_password": password},
    )
    assert r.status_code == 201
    assert r.json()["email"] == address

    login = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": mixed, "password": password},
    )
    assert login.status_code == 200
    again = await client.post(
        f"{settings.API_V1_STR}/users/signup/complete",
        json={"token": signup_token(address), "new_password": password},
    )
    assert again.status_code == 400
    with patch("src.notifications.service.send_email") as send:
        await client.post(
            f"{settings.API_V1_STR}/password-recovery", json={"email": mixed}
        )
    assert len(sent_to(send, address)) == 1


async def test_completing_a_signup_that_loses_the_race_answers_400(
    client: AsyncClient, db: AsyncSession
) -> None:
    taken, _, _ = await user_with_headers(client, db)

    with patch("src.users.service.get_user_by_email", return_value=None):
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup/complete",
            json={
                "token": signup_token(taken.email),
                "new_password": random_lower_string(),
            },
        )

    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"


async def test_confirming_an_email_change_that_loses_the_race_answers_400(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, _, _ = await user_with_headers(client, db)
    taken, _, _ = await user_with_headers(client, db)
    original_email, original_version = user.email, user.token_version
    token = generate_email_token(
        audience=EMAIL_CHANGE_AUDIENCE,
        claims={"sub": str(user.id), "email": taken.email, "from": user.email},
        expires_in=timedelta(hours=1),
    )

    with patch("src.users.service.get_user_by_email", return_value=None):
        r = await client.post(
            f"{settings.API_V1_STR}/users/confirm-email", json={"token": token}
        )

    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"
    await db.refresh(user)
    assert (user.email, user.token_version) == (original_email, original_version)
