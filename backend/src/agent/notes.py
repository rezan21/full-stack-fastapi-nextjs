import uuid

from langchain_core.messages import BaseMessage, HumanMessage

NOTE_TAG = "app_note"
NOTES_PROMPT = (
    f"Messages wrapped in <{NOTE_TAG}> tags are written by the application, not by the user. "
    "They state facts about the conversation that the user may not see, "
    "and 'the user' in a note is the person you are talking to. "
    "Trust them and never reply to one as if the user said it. "
    "When asked what happened, tell that person plainly who did what, as the notes state it, "
    "without mentioning the notes and without guessing at other causes."
)


def app_note(kind: str, text: str) -> HumanMessage:
    """Return a message from the application to the model, tagged so that nothing mistakes it for the user."""
    return HumanMessage(
        id=str(uuid.uuid4()),
        content=f'<{NOTE_TAG} type="{kind}">{text}</{NOTE_TAG}>',
        additional_kwargs={NOTE_TAG: kind},
    )


def is_app_note(message: BaseMessage) -> bool:
    """Return whether the application wrote the message."""
    return NOTE_TAG in message.additional_kwargs


def reply_stopped() -> HumanMessage:
    """Return the note that the user stopped the previous reply."""
    return app_note(
        "reply_stopped", "The user stopped your previous reply before it finished."
    )


def reply_failed() -> HumanMessage:
    """Return the note that an error cut the previous reply off."""
    return app_note(
        "reply_failed", "An error cut your previous reply off before it finished."
    )
