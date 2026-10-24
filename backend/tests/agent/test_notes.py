from langchain_core.messages import HumanMessage

from src.agent import notes


def test_an_application_note_carries_its_kind_in_a_tag() -> None:
    note = notes.app_note("a_kind", "something happened")

    assert note.content == '<app_note type="a_kind">something happened</app_note>'


def test_an_application_note_is_recognized_and_a_user_message_is_not() -> None:
    assert notes.is_app_note(notes.app_note("a_kind", "something happened"))
    assert not notes.is_app_note(HumanMessage(content="something happened"))


def test_two_notes_of_the_same_kind_are_different_messages() -> None:
    assert notes.app_note("a_kind", "x").id != notes.app_note("a_kind", "x").id
