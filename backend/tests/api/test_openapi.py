import json
from pathlib import Path

import pytest

from app.main import app
from app.models import EMAIL_PATTERN

SPEC_PATH = Path(__file__).parents[2] / "openapi.json"


def test_committed_openapi_spec_is_current() -> None:
    committed = json.loads(SPEC_PATH.read_text())
    current = json.loads(json.dumps(app.openapi()))
    message = "OpenAPI spec is stale: run scripts/generate-client.sh"
    assert committed["paths"] == current["paths"], message
    assert committed["components"] == current["components"], message


def current_schemas() -> dict[str, dict]:
    return json.loads(json.dumps(app.openapi()))["components"]["schemas"]


def test_login_body_is_just_the_credentials() -> None:
    assert set(current_schemas()["Credentials"]["properties"]) == {
        "username",
        "password",
    }


def test_email_fields_carry_the_pattern_the_server_enforces() -> None:
    schemas = current_schemas()
    fields = [
        schemas["Credentials"]["properties"]["username"],
        schemas["EmailChange"]["properties"]["email"],
        schemas["PasswordRecovery"]["properties"]["email"],
        schemas["UserRegister"]["properties"]["email"],
    ]
    assert [field["pattern"] for field in fields] == [EMAIL_PATTERN] * len(fields)


@pytest.mark.parametrize("name", ["ItemPublic", "ItemsPublic", "Token", "UserPublic"])
def test_response_models_require_every_field_and_carry_no_input_limits(
    name: str,
) -> None:
    schema = current_schemas()[name]
    assert set(schema["required"]) == set(schema["properties"])
    for field in schema["properties"].values():
        assert not {"minLength", "maxLength", "pattern"} & set(field)
