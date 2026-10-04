from app.utils import event_scrubber

FILTERED = "[Filtered]"


def scrubbed(data: dict[str, str]) -> dict[str, str]:
    event = {"request": {"data": data}}
    event_scrubber().scrub_event(event)
    return {
        key: getattr(value, "value", value)
        for key, value in event["request"]["data"].items()
    }


def test_the_password_and_token_fields_are_hidden() -> None:
    data = scrubbed(
        {
            "new_password": "a",
            "current_password": "b",
            "access_token": "c",
            "password": "d",
            "token": "e",
        }
    )
    assert set(data.values()) == {FILTERED}


def test_other_fields_are_kept() -> None:
    assert scrubbed({"email": "a@example.com"}) == {"email": "a@example.com"}
