import pytest
from ag_ui.core import EventType
from ag_ui_langgraph import LangGraphAgent
from langgraph.checkpoint.memory import InMemorySaver

from src.agent import factory as agent_factory
from src.agent import notes
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from tests.utils.agent import (
    CONTEXT,
    PROVIDER_ERROR,
    THREAD,
    PartialModel,
    RecordingModel,
    agent_for,
    collect,
    replying,
    run_input,
    stop_midway,
)


async def remembered(agent: LangGraphAgent) -> list[tuple[str, str]]:
    state = await agent.graph.aget_state(agent_threads.thread_config(THREAD))
    return [(m.type, str(m.content)) for m in state.values["messages"]]


async def test_a_reply_cut_off_midway_is_kept_in_the_agent_memory_with_a_note() -> None:
    model = PartialModel(chunks=["Once upon ", "a time"])
    agent = agent_for(model)

    await stop_midway(agent, run_input("tell me a story"), len(model.chunks))

    assert await remembered(agent) == [
        ("human", "tell me a story"),
        ("ai", "Once upon a time"),
        ("human", notes.reply_stopped().content),
    ]


async def test_the_next_run_sees_the_cut_off_reply_and_that_it_was_stopped() -> None:
    saver = InMemorySaver()
    model = PartialModel(chunks=["Once upon ", "a time"])
    await stop_midway(
        agent_factory.build_agent(model, saver),
        run_input("tell me a story"),
        len(model.chunks),
    )
    recorder = RecordingModel()

    await collect(
        agent_streaming.stream_events(
            agent_factory.build_agent(recorder, saver), run_input("continue"), CONTEXT
        )
    )

    assert [(m.type, m.content) for m in recorder.seen[0] if m.type != "system"] == [
        ("human", "tell me a story"),
        ("ai", "Once upon a time"),
        ("human", notes.reply_stopped().content),
        ("human", "continue"),
    ]


async def test_the_model_is_told_what_the_applications_notes_are() -> None:
    recorder = RecordingModel()

    await collect(
        agent_streaming.stream_events(agent_for(recorder), run_input("hi"), CONTEXT)
    )

    system = next(m for m in recorder.seen[0] if m.type == "system")
    assert f"<{notes.NOTE_TAG}>" in str(system.content)


async def test_a_reply_that_fails_midway_is_kept_in_the_agent_memory_with_a_note() -> (
    None
):
    agent = agent_for(PartialModel(chunks=["Once upon ", "a time"], then_fail=True))

    events = await collect(
        agent_streaming.stream_events(agent, run_input("tell me a story"), CONTEXT)
    )

    assert events[-1].type == EventType.RUN_ERROR
    assert await remembered(agent) == [
        ("human", "tell me a story"),
        ("ai", "Once upon a time"),
        ("human", notes.reply_failed().content),
    ]


async def test_history_leaves_out_the_applications_notes() -> None:
    model = PartialModel(chunks=["Once upon ", "a time"])
    agent = agent_for(model)
    await stop_midway(agent, run_input("tell me a story"), len(model.chunks))

    history = await agent_threads.read_history(agent, THREAD)

    assert [(m.role, m.content) for m in history] == [
        ("user", "tell me a story"),
        ("assistant", "Once upon a time"),
    ]


async def test_a_reply_that_is_already_in_the_agent_memory_is_not_added_again() -> None:
    agent = agent_for(replying("Hello there!"))
    await collect(agent_streaming.stream_events(agent, run_input("hi"), CONTEXT))
    reply = (await agent_threads.read_history(agent, THREAD))[-1]

    await agent_streaming.keep_streamed_text(
        agent, THREAD, {reply.id: reply.content}, notes.reply_stopped()
    )

    assert len(await remembered(agent)) == 2


async def test_text_is_not_added_when_no_model_call_was_cut_off() -> None:
    agent = agent_for(replying("Hello there!"))
    await collect(agent_streaming.stream_events(agent, run_input("hi"), CONTEXT))

    await agent_streaming.keep_streamed_text(
        agent, THREAD, {"unknown": "text"}, notes.reply_stopped()
    )

    assert len(await remembered(agent)) == 2


async def test_a_failure_to_keep_the_reply_is_logged_and_does_not_break_the_stream(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def on_finished() -> None:
        raise RuntimeError(PROVIDER_ERROR)

    model = PartialModel(chunks=["Once upon ", "a time"])

    await stop_midway(
        agent_for(model), run_input("tell me a story"), len(model.chunks), on_finished
    )

    assert "Could not keep an unfinished reply" in caplog.text
