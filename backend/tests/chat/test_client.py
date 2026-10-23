import uuid
from typing import Any

import pytest
from ag_ui.core import EventType, RunErrorEvent
from ag_ui_langgraph import LangGraphAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.chat import client as chat_client
from src.chat import service as chat_service
from src.chat.exceptions import InvalidChatInput
from src.chat.schemas import MAX_MESSAGE_CHARS, AgentMessage
from tests.utils.chat import (
    PROVIDER_ERROR,
    ExplodingModel,
    LoopingToolModel,
    ScriptedModel,
    client_input,
    collect,
    replying,
)

CONVERSATION = uuid.uuid4()
OTHER_CONVERSATION = uuid.uuid4()


def agent_for(model: BaseChatModel) -> LangGraphAgent:
    return chat_client.build_agent(model, InMemorySaver())


def run_input(text: str, conversation: uuid.UUID = CONVERSATION) -> Any:
    return chat_service.build_run_input(
        client_input(messages=[{"id": "m1", "role": "user", "content": text}]),
        conversation,
    )


def types(events: list[Any]) -> list[EventType]:
    return [event.type for event in events]


def reply_text(events: list[Any]) -> str:
    return "".join(
        event.delta for event in events if event.type == EventType.TEXT_MESSAGE_CONTENT
    )


def test_only_the_newest_user_message_is_kept() -> None:
    result = chat_service.build_run_input(client_input(), CONVERSATION)

    assert [(m.role, m.content) for m in result.messages] == [
        ("user", "newest question")
    ]


def test_the_run_belongs_to_the_conversation_and_not_the_thread_the_client_names() -> (
    None
):
    result = chat_service.build_run_input(client_input(), CONVERSATION)

    assert result.thread_id == str(CONVERSATION)


def test_the_message_gets_a_new_id_made_by_the_server() -> None:
    first = chat_service.build_run_input(client_input(), CONVERSATION)
    second = chat_service.build_run_input(client_input(), CONVERSATION)

    assert first.messages[0].id not in {"m1", "m2", "m3"}
    assert first.messages[0].id != second.messages[0].id


def test_everything_the_client_could_steer_the_run_with_is_dropped() -> None:
    result = chat_service.build_run_input(client_input(), CONVERSATION)

    assert not result.state
    assert not result.tools
    assert not result.context
    assert not result.forwarded_props
    assert not result.resume


def test_a_short_run_id_is_kept() -> None:
    assert chat_service.build_run_input(client_input(), CONVERSATION).run_id == "run-1"


def test_an_overlong_run_id_is_replaced() -> None:
    result = chat_service.build_run_input(client_input(runId="r" * 101), CONVERSATION)

    assert result.run_id != "r" * 101
    assert len(result.run_id) <= chat_service.RUN_ID_MAX_LENGTH


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
        chat_service.build_run_input(client_input(messages=messages), CONVERSATION)


def test_a_message_at_the_length_limit_is_accepted_and_one_over_is_not() -> None:
    at_limit = "x" * MAX_MESSAGE_CHARS
    accepted = run_input(at_limit)
    assert accepted.messages[0].content == at_limit

    with pytest.raises(InvalidChatInput):
        run_input(at_limit + "x")


async def test_the_reply_streams_as_text_events_without_raw_internals() -> None:
    events = await collect(
        chat_client.stream_events(agent_for(replying("Hello there!")), run_input("hi"))
    )

    assert types(events)[0] == EventType.RUN_STARTED
    assert types(events)[-1] == EventType.RUN_FINISHED
    assert reply_text(events) == "Hello there!"
    assert EventType.RAW not in types(events)


async def test_a_provider_error_reaches_the_client_only_as_a_generic_message() -> None:
    events = await collect(
        chat_client.stream_events(
            agent_for(ExplodingModel(messages=iter([]))), run_input("hi")
        )
    )

    final = events[-1]
    assert isinstance(final, RunErrorEvent)
    assert final.message == chat_client.GENERIC_ERROR
    serialized = " ".join(event.model_dump_json() for event in events)
    assert "sk-proj" not in serialized
    assert PROVIDER_ERROR not in serialized


async def test_a_failure_before_the_run_starts_still_gets_a_start_and_a_generic_error() -> (
    None
):
    class Broken:
        def clone(self) -> Broken:
            return self

        async def run(self, run_input: Any) -> Any:
            raise RuntimeError(PROVIDER_ERROR)
            yield

    events = await collect(chat_client.stream_events(Broken(), run_input("hi")))  # type: ignore[arg-type]

    assert types(events) == [EventType.RUN_STARTED, EventType.RUN_ERROR]
    assert events[-1].message == chat_client.GENERIC_ERROR  # type: ignore[attr-defined]


async def test_a_runaway_agent_is_stopped_by_the_recursion_limit() -> None:
    model = LoopingToolModel()

    events = await collect(
        chat_client.stream_events(agent_for(model), run_input("loop forever"))
    )

    assert types(events)[-1] == EventType.RUN_ERROR
    assert model.calls <= chat_client.RECURSION_LIMIT


async def test_history_lists_the_user_and_assistant_text_of_a_conversation() -> None:
    agent = agent_for(replying("First answer.", "Second answer."))
    for text in ("one", "two"):
        await collect(chat_client.stream_events(agent, run_input(text)))

    history = await chat_client.read_history(agent, CONVERSATION)

    assert [(m.role, m.content) for m in history] == [
        ("user", "one"),
        ("assistant", "First answer."),
        ("user", "two"),
        ("assistant", "Second answer."),
    ]


async def test_history_leaves_out_tool_calls_and_their_results() -> None:
    model = ScriptedModel(
        replies=[
            AIMessage(
                content="",
                tool_calls=[{"name": "ls", "args": {"path": "/"}, "id": "call-1"}],
            ),
            AIMessage(content="All done."),
        ]
    )
    agent = agent_for(model)
    await collect(chat_client.stream_events(agent, run_input("look around")))

    history = await chat_client.read_history(agent, CONVERSATION)

    assert [(m.role, m.content) for m in history] == [
        ("user", "look around"),
        ("assistant", "All done."),
    ]


async def test_conversations_do_not_see_each_others_history() -> None:
    agent = agent_for(replying("For the first.", "For the other."))
    await collect(chat_client.stream_events(agent, run_input("private to one")))
    await collect(
        chat_client.stream_events(
            agent, run_input("private to two", OTHER_CONVERSATION)
        )
    )

    first = await chat_client.read_history(agent, CONVERSATION)
    other = await chat_client.read_history(agent, OTHER_CONVERSATION)

    assert [m.content for m in first] == ["private to one", "For the first."]
    assert [m.content for m in other] == ["private to two", "For the other."]


async def test_a_conversation_that_never_ran_has_no_history() -> None:
    assert await chat_client.read_history(agent_for(replying()), uuid.uuid4()) == []


async def test_deleted_conversations_are_forgotten() -> None:
    saver = InMemorySaver()
    agent = chat_client.build_agent(replying("kept", "gone"), saver)
    await collect(chat_client.stream_events(agent, run_input("one")))
    await collect(
        chat_client.stream_events(agent, run_input("two", OTHER_CONVERSATION))
    )

    await chat_client.delete_threads(saver, [CONVERSATION])

    assert await chat_client.read_history(agent, CONVERSATION) == []
    assert await chat_client.read_history(agent, OTHER_CONVERSATION) != []


def agent_said(agent_id: str, role: str, content: str) -> AgentMessage:
    return AgentMessage(id=agent_id, role=role, content=content)  # type: ignore[arg-type]


def test_the_replies_are_what_the_assistant_said_after_the_message_it_answers() -> None:
    history = [
        agent_said("u-1", "user", "an old question"),
        agent_said("a-1", "assistant", "an old answer"),
        agent_said("u-2", "user", "the new question"),
        agent_said("a-2", "assistant", "I will look"),
        agent_said("a-3", "assistant", "the final answer"),
    ]

    replies = chat_service.replies_after(history, "u-2")

    assert [reply.id for reply in replies] == ["a-2", "a-3"]


def test_a_message_that_is_not_in_the_history_has_no_replies() -> None:
    history = [agent_said("u-1", "user", "hi"), agent_said("a-1", "assistant", "hello")]

    assert chat_service.replies_after(history, "missing") == []


async def test_the_finish_hook_runs_before_the_client_is_told_the_run_finished() -> (
    None
):
    order: list[str] = []

    async def on_finished() -> None:
        order.append("saved")

    async def stream() -> None:
        async for event in chat_client.stream_events(
            agent_for(replying("Hello there!")), run_input("hi"), on_finished
        ):
            order.append(event.type.value)

    await stream()

    assert order[-2:] == ["saved", "RUN_FINISHED"]
    assert order.count("saved") == 1


async def test_the_finish_hook_does_not_run_when_the_run_fails() -> None:
    called: list[str] = []

    async def on_finished() -> None:
        called.append("saved")

    events = await collect(
        chat_client.stream_events(
            agent_for(ExplodingModel(messages=iter([]))), run_input("hi"), on_finished
        )
    )

    assert events[-1].type == EventType.RUN_ERROR
    assert called == []


async def test_a_run_whose_answer_could_not_be_saved_ends_in_a_generic_error() -> None:
    async def on_finished() -> None:
        raise RuntimeError(PROVIDER_ERROR)

    events = await collect(
        chat_client.stream_events(
            agent_for(replying("Hello there!")), run_input("hi"), on_finished
        )
    )

    assert types(events)[-1] == EventType.RUN_ERROR
    assert EventType.RUN_FINISHED not in types(events)
    assert events[-1].message == chat_client.GENERIC_ERROR  # type: ignore[attr-defined]
    assert PROVIDER_ERROR not in " ".join(e.model_dump_json() for e in events)
