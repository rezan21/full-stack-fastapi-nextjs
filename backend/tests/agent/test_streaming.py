from typing import Any

from ag_ui.core import EventType, RunErrorEvent

from src.agent import factory as agent_factory
from src.agent import streaming as agent_streaming
from tests.utils.agent import (
    CONTEXT,
    PROVIDER_ERROR,
    THREAD,
    ExplodingModel,
    LoopingToolModel,
    agent_for,
    collect,
    replying,
    run_input,
)


def types(events: list[Any]) -> list[EventType]:
    return [event.type for event in events]


def reply_text(events: list[Any]) -> str:
    return "".join(
        event.delta for event in events if event.type == EventType.TEXT_MESSAGE_CONTENT
    )


def test_a_run_answers_the_text_it_is_given_in_the_thread_it_is_given() -> None:
    result = run_input("a question", THREAD)

    assert result.thread_id == THREAD
    assert [(m.role, m.content) for m in result.messages] == [("user", "a question")]


def test_the_message_gets_a_new_id_made_by_the_server() -> None:
    first = run_input("a question")
    second = run_input("a question")

    assert first.messages[0].id != second.messages[0].id


def test_a_run_carries_nothing_a_client_could_steer_it_with() -> None:
    result = run_input("a question")

    assert not result.state
    assert not result.tools
    assert not result.context
    assert not result.forwarded_props
    assert not result.resume


def test_a_short_run_id_is_kept() -> None:
    assert run_input("hi").run_id == "run-1"


def test_an_overlong_run_id_is_replaced() -> None:
    result = run_input("hi", run_id="r" * 101)

    assert result.run_id != "r" * 101
    assert len(result.run_id) <= agent_streaming.RUN_ID_MAX_LENGTH


async def test_the_reply_streams_as_text_events_without_raw_internals() -> None:
    events = await collect(
        agent_streaming.stream_events(
            agent_for(replying("Hello there!")), run_input("hi"), CONTEXT
        )
    )

    assert types(events)[0] == EventType.RUN_STARTED
    assert types(events)[-1] == EventType.RUN_FINISHED
    assert reply_text(events) == "Hello there!"
    assert EventType.RAW not in types(events)


async def test_a_provider_error_reaches_the_client_only_as_a_generic_message() -> None:
    events = await collect(
        agent_streaming.stream_events(
            agent_for(ExplodingModel(messages=iter([]))), run_input("hi"), CONTEXT
        )
    )

    final = events[-1]
    assert isinstance(final, RunErrorEvent)
    assert final.message == agent_streaming.GENERIC_ERROR
    serialized = " ".join(event.model_dump_json() for event in events)
    assert "sk-proj" not in serialized
    assert PROVIDER_ERROR not in serialized


async def test_a_failure_before_the_run_starts_still_gets_a_start_and_a_generic_error() -> (
    None
):
    class Broken:
        config: dict[str, Any] = {}

        def clone(self) -> Broken:
            return self

        async def run(self, run_input: Any) -> Any:
            raise RuntimeError(PROVIDER_ERROR)
            yield

    events = await collect(
        agent_streaming.stream_events(Broken(), run_input("hi"), CONTEXT)  # type: ignore[arg-type]
    )

    assert types(events) == [EventType.RUN_STARTED, EventType.RUN_ERROR]
    assert events[-1].message == agent_streaming.GENERIC_ERROR  # type: ignore[attr-defined]


async def test_a_runaway_agent_is_stopped_by_the_recursion_limit() -> None:
    model = LoopingToolModel()

    events = await collect(
        agent_streaming.stream_events(
            agent_for(model), run_input("loop forever"), CONTEXT
        )
    )

    assert types(events)[-1] == EventType.RUN_ERROR
    assert model.calls <= agent_factory.RECURSION_LIMIT


async def test_the_finish_hook_runs_before_the_client_is_told_the_run_finished() -> (
    None
):
    order: list[str] = []

    async def on_finished() -> None:
        order.append("saved")

    async for event in agent_streaming.stream_events(
        agent_for(replying("Hello there!")), run_input("hi"), CONTEXT, on_finished
    ):
        order.append(event.type.value)

    assert order[-2:] == ["saved", "RUN_FINISHED"]
    assert order.count("saved") == 1


async def test_the_finish_hook_does_not_run_when_the_run_fails() -> None:
    called: list[str] = []

    async def on_finished() -> None:
        called.append("saved")

    events = await collect(
        agent_streaming.stream_events(
            agent_for(ExplodingModel(messages=iter([]))),
            run_input("hi"),
            CONTEXT,
            on_finished,
        )
    )

    assert events[-1].type == EventType.RUN_ERROR
    assert called == []


async def test_a_run_whose_answer_could_not_be_saved_ends_in_a_generic_error() -> None:
    async def on_finished() -> None:
        raise RuntimeError(PROVIDER_ERROR)

    events = await collect(
        agent_streaming.stream_events(
            agent_for(replying("Hello there!")), run_input("hi"), CONTEXT, on_finished
        )
    )

    assert types(events)[-1] == EventType.RUN_ERROR
    assert EventType.RUN_FINISHED not in types(events)
    assert events[-1].message == agent_streaming.GENERIC_ERROR  # type: ignore[attr-defined]
    assert PROVIDER_ERROR not in " ".join(e.model_dump_json() for e in events)
