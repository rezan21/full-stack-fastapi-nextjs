import pytest
from pydantic import ValidationError

from app.models import Credentials, EmailChange, PasswordRecovery, UserRegister


@pytest.mark.parametrize(
    "email",
    [
        "a@b.co",
        "Ab.c+d@Sub.Example.com",
        "user@example.test",
        "o'neil@example.org",
    ],
)
def test_every_email_field_accepts_the_same_addresses(email: str) -> None:
    lowered = email.lower()
    assert UserRegister(email=email, full_name="x").email == lowered
    assert PasswordRecovery(email=email).email == lowered
    assert EmailChange(email=email, current_password="x").email == lowered
    assert Credentials(username=email, password="x").username == lowered


@pytest.mark.parametrize(
    "email",
    [
        "first/last@example.com",
        "üser@example.com",
        "a@b",
        "a..b@example.com",
        ".a@example.com",
        "a@-example.com",
        "a@example.c",
        "a@example.com ",
    ],
)
def test_every_email_field_rejects_the_same_addresses(email: str) -> None:
    with pytest.raises(ValidationError):
        UserRegister(email=email, full_name="x")
    with pytest.raises(ValidationError):
        PasswordRecovery(email=email)
    with pytest.raises(ValidationError):
        EmailChange(email=email, current_password="x")
    with pytest.raises(ValidationError):
        Credentials(username=email, password="x")
