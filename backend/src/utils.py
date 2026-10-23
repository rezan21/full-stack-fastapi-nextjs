from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

SECRET_FIELDS = [
    "new_password",
    "current_password",
    "access_token",
    "messages",
    "content",
]


def event_scrubber() -> EventScrubber:
    """Build the Sentry scrubber that also hides the password and token fields."""
    return EventScrubber(denylist=[*DEFAULT_DENYLIST, *SECRET_FIELDS], recursive=True)


def describe_duration(minutes: int) -> str:
    """Describe a duration in minutes for an email."""
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hour{'' if hours == 1 else 's'}"
    return f"{minutes} minute{'' if minutes == 1 else 's'}"
