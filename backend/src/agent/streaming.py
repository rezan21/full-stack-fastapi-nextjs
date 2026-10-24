import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import aclosing

import anyio
from ag_ui.core import (
    BaseEvent,
    EventType,
    Message,
    ResumeEntry,
    RunAgentInput,
    RunErrorEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    Tool,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
from ag_ui_langgraph import LangGraphAgent
from langchain_core.messages import AIMessage, HumanMessage

from src.agent import threads as agent_threads
from src.agent.context import AgentContext
from src.agent.notes import reply_failed, reply_stopped

RUN_ID_MAX_LENGTH = 100
CALL_ANNOUNCEMENTS = (ToolCallStartEvent, ToolCallArgsEvent, ToolCallEndEvent)
GENERIC_ERROR = "The assistant ran into a problem. Please try again."

logger = logging.getLogger(__name__)


def build_run_input(
    thread_id: str,
    run_id: str,
    messages: list[Message],
    tools: Sequence[Tool] = (),
    resume: Sequence[ResumeEntry] = (),
) -> RunAgentInput:
    """Return the input of a run with these messages, browser tools and answers, and nothing else to steer it."""
    return RunAgentInput(
        thread_id=thread_id,
        run_id=run_id if len(run_id) <= RUN_ID_MAX_LENGTH else str(uuid.uuid4()),
        messages=messages,
        state={},
        tools=list(tools),
        context=[],
        forwarded_props={},
        resume=list(resume) or None,
    )


def run_for(agent: LangGraphAgent, context: AgentContext) -> LangGraphAgent:
    """Return a copy of the agent whose run is made for the context."""
    run_agent = agent.clone()
    configurable = run_agent.config.get("configurable", {})
    run_agent.config = {
        **run_agent.config,
        "configurable": {**configurable, **context.model_dump(mode="json")},
    }
    return run_agent


async def stream_events(
    agent: LangGraphAgent,
    run_input: RunAgentInput,
    context: AgentContext,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> AsyncIterator[BaseEvent]:
    """Stream a run's events, hiding the details of any failure from the client."""
    started = False
    finished = False
    failed = False
    streamed: dict[str, str] = {}
    resumed_calls = await agent_threads.interrupted_tool_call_ids(
        agent,
        run_input.thread_id,
        {entry.interrupt_id for entry in run_input.resume or []},
    )
    try:
        async with aclosing(run_for(agent, context).run(run_input)) as events:
            async for event in events:
                if (
                    isinstance(event, CALL_ANNOUNCEMENTS)
                    and event.tool_call_id in resumed_calls
                ):
                    continue
                started = started or event.type == EventType.RUN_STARTED
                if isinstance(event, TextMessageContentEvent):
                    text = streamed.get(event.message_id, "")
                    streamed[event.message_id] = text + event.delta
                if event.type == EventType.RUN_ERROR:
                    failed = True
                    yield event.model_copy(update={"message": GENERIC_ERROR})
                    continue
                if event.type == EventType.RUN_FINISHED:
                    finished = True
                    if on_finished:
                        await on_finished()
                yield event
    except Exception:
        logger.exception("Chat run failed")
        failed = True
        if not started:
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=run_input.thread_id,
                run_id=run_input.run_id,
            )
        yield RunErrorEvent(type=EventType.RUN_ERROR, message=GENERIC_ERROR)
    finally:
        if streamed and not finished:
            with anyio.CancelScope(shield=True):
                await settle_unfinished_run(
                    agent,
                    run_input.thread_id,
                    streamed,
                    reply_failed() if failed else reply_stopped(),
                    on_finished,
                )


async def settle_unfinished_run(
    agent: LangGraphAgent,
    thread_id: str,
    streamed: dict[str, str],
    note: HumanMessage,
    on_finished: Callable[[], Awaitable[None]] | None,
) -> None:
    """Keep what an unfinished run streamed, in the agent's memory and the transcript."""
    try:
        await keep_streamed_text(agent, thread_id, streamed, note)
        if on_finished:
            await on_finished()
    except Exception:
        logger.exception("Could not keep an unfinished reply")


async def keep_streamed_text(
    agent: LangGraphAgent,
    thread_id: str,
    streamed: dict[str, str],
    note: HumanMessage,
) -> None:
    """Add the text a cut-off model call streamed to the agent's memory, followed by a note saying why it was cut off."""
    config = agent_threads.thread_config(thread_id)
    state = await agent.graph.aget_state(config)
    remembered = {message.id for message in (state.values or {}).get("messages", [])}
    unsaved = [
        AIMessage(id=message_id, content=text)
        for message_id, text in streamed.items()
        if message_id not in remembered and text.strip()
    ]
    if unsaved and state.next:
        await agent.graph.aupdate_state(
            config, {"messages": [*unsaved, note]}, as_node=state.next[0]
        )
