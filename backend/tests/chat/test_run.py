from typing import Any

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.chat import service as chat_service
from src.chat.exceptions import InvalidChatInput
from src.chat.models import Conversation
from src.chat.schemas import MAX_MESSAGE_CHARS
from tests.utils.chat import client_input
from tests.utils.user import create_random_user


@pytest.fixture
async def conversation(db: AsyncSession) -> Conversation:
    created = Conversation(owner_id=(await create_random_user(db)).id)
    db.add(created)
    await db.commit()
    return created


def one_message(text: str) -> Any:
    return client_input(messages=[{"id": "m1", "role": "user", "content": text}])


def test_the_text_of_a_run_is_the_newest_user_message() -> None:
    assert chat_service.newest_user_text(client_input()) == "newest question"


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"id": "a", "role": "assistant", "content": "only the assistant"}],
        [{"id": "a", "role": "user", "content": ""}],
        [{"id": "a", "role": "user", "content": "   \n\t"}],
        [
            {
                "id": "a",
                "role": "user",
                "content": [{"type": "text", "text": "not a plain string"}],
            }
        ],
    ],
)
def test_input_without_a_plain_text_user_message_is_refused(
    messages: list[dict[str, Any]],
) -> None:
    with pytest.raises(InvalidChatInput):
        chat_service.newest_user_text(client_input(messages=messages))


def test_a_message_at_the_length_limit_is_accepted_and_one_over_is_not() -> None:
    at_limit = "x" * MAX_MESSAGE_CHARS

    assert chat_service.newest_user_text(one_message(at_limit)) == at_limit
    with pytest.raises(InvalidChatInput):
        chat_service.newest_user_text(one_message(at_limit + "x"))


async def test_a_run_belongs_to_the_conversation_and_not_the_thread_the_client_names(
    db: AsyncSession, conversation: Conversation
) -> None:
    run_input = await chat_service.start_run(db, conversation, client_input())

    assert run_input.thread_id == str(conversation.id)


async def test_a_run_answers_only_the_newest_user_message(
    db: AsyncSession, conversation: Conversation
) -> None:
    run_input = await chat_service.start_run(db, conversation, client_input())

    assert [(m.role, m.content) for m in run_input.messages] == [
        ("user", "newest question")
    ]


async def test_everything_the_client_could_steer_the_run_with_is_dropped(
    db: AsyncSession, conversation: Conversation
) -> None:
    run_input = await chat_service.start_run(db, conversation, client_input())

    assert not run_input.state
    assert not run_input.tools
    assert not run_input.context
    assert not run_input.forwarded_props
    assert not run_input.resume
