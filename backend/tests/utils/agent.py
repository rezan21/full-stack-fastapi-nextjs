import asyncio
import json
import uuid
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterator,
    Sequence,
)
from contextlib import contextmanager
from typing import Any, Self

import anyio
from ag_ui.core import (
    BaseEvent,
    EventType,
    Interrupt,
    ResumeEntry,
    RunAgentInput,
    RunFinishedEvent,
    RunFinishedInterruptOutcome,
    Tool,
    ToolCallResultEvent,
    ToolMessage,
    UserMessage,
)
from ag_ui_langgraph import LangGraphAgent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import Field

from src.agent import factory as agent_factory
from src.agent import streaming as agent_streaming
from src.agent.context import AgentContext
from src.agent.dependencies import get_runtime
from src.agent.runtime import AgentRuntime
from src.items.models import Item
from src.main import app
from src.users.models import User

PROVIDER_ERROR = "Incorrect API key provided: sk-proj-secret1234 for org-abc"
CONTEXT = AgentContext(user_id=uuid.uuid4())
THREAD = str(uuid.uuid4())
OTHER_THREAD = str(uuid.uuid4())


class FakeChatModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self


class ExplodingModel(FakeChatModel):
    def _generate(self, *args: Any, **kwargs: Any) -> ChatResult:
        raise RuntimeError(PROVIDER_ERROR)

    async def _agenerate(self, *args: Any, **kwargs: Any) -> ChatResult:
        raise RuntimeError(PROVIDER_ERROR)


class LoopingToolModel(BaseChatModel):
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "looping-tool"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self

    def _generate(self, *args: Any, **kwargs: Any) -> ChatResult:
        self.calls += 1
        message = AIMessage(
            content="",
            tool_calls=[
                {"name": "ls", "args": {"path": "/"}, "id": f"call-{self.calls}"}
            ],
        )
        return ChatResult(generations=[ChatGeneration(message=message)])


def replying(*texts: str) -> FakeChatModel:
    return FakeChatModel(messages=iter([AIMessage(content=text) for text in texts]))


def agent_for(model: BaseChatModel) -> LangGraphAgent:
    return agent_factory.build_agent(model, InMemorySaver())


def run_input(
    text: str,
    thread_id: str = THREAD,
    tools: Sequence[Tool] = (),
    run_id: str = "run-1",
) -> RunAgentInput:
    message = UserMessage(id=str(uuid.uuid4()), role="user", content=text)
    return agent_streaming.build_run_input(thread_id, run_id, [message], tools)


def resume_input(
    answers: Sequence[ResumeEntry], run_id: str = "run-2"
) -> RunAgentInput:
    return agent_streaming.build_run_input(THREAD, run_id, [], resume=answers)


def browser_answer_input(
    content: str,
    tools: Sequence[Tool] = (),
    tool_call_id: str = "call-1",
    thread_id: str = THREAD,
) -> RunAgentInput:
    message = ToolMessage(
        id=str(uuid.uuid4()), role="tool", content=content, tool_call_id=tool_call_id
    )
    return agent_streaming.build_run_input(thread_id, "r2", [message], tools)


async def collect(stream: AsyncIterator[BaseEvent]) -> list[BaseEvent]:
    return [event async for event in stream]


def tool_results(events: list[BaseEvent]) -> list[dict[str, Any]]:
    return [
        json.loads(str(e.content)) for e in events if isinstance(e, ToolCallResultEvent)
    ]


async def stop_midway(
    agent: LangGraphAgent,
    run_input: RunAgentInput,
    deltas: int,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> None:
    seen = 0
    with anyio.CancelScope() as scope:
        async for event in agent_streaming.stream_events(
            agent, run_input, CONTEXT, on_finished
        ):
            if event.type == EventType.TEXT_MESSAGE_CONTENT:
                seen += 1
                if seen == deltas:
                    scope.cancel()


class ScriptedModel(BaseChatModel):
    replies: list[AIMessage]
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self

    def _generate(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> ChatResult:
        self.seen.append(list(messages))
        return ChatResult(generations=[ChatGeneration(message=self.replies.pop(0))])


class StreamingScriptedModel(ScriptedModel):
    def _stream(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> Iterator[ChatGenerationChunk]:
        self.seen.append(list(messages))
        reply = self.replies.pop(0)
        chunk = AIMessageChunk(content=reply.content, tool_calls=reply.tool_calls)
        yield ChatGenerationChunk(message=chunk)


def tool_call(name: str, args: dict[str, Any], call_id: str = "call-1") -> Any:
    return {"name": name, "args": args, "id": call_id}


def calling(calls: list[Any], *texts: str) -> StreamingScriptedModel:
    replies = [AIMessage(content="", tool_calls=calls)]
    return StreamingScriptedModel(
        replies=[*replies, *(AIMessage(content=t) for t in texts)]
    )


def deleting(
    *items: Item, texts: tuple[str, ...] = ("done",)
) -> StreamingScriptedModel:
    calls = [
        tool_call("delete_item", {"item_id": str(item.id)}, f"call-{number}")
        for number, item in enumerate(items)
    ]
    return calling(calls, *texts)


async def run_as(
    owner: User, agent: LangGraphAgent, run: RunAgentInput
) -> list[BaseEvent]:
    return await collect(
        agent_streaming.stream_events(agent, run, AgentContext(user_id=owner.id))
    )


async def ask_to_delete(
    owner: User, model: StreamingScriptedModel
) -> tuple[LangGraphAgent, list[BaseEvent]]:
    agent = agent_for(model)
    return agent, await run_as(owner, agent, run_input("delete it"))


def interrupts_of(events: list[BaseEvent]) -> list[Interrupt]:
    finished = events[-1]
    assert isinstance(finished, RunFinishedEvent)
    assert isinstance(finished.outcome, RunFinishedInterruptOutcome)
    return finished.outcome.interrupts


def answer(interrupt: Interrupt, approved: bool | None) -> ResumeEntry:
    if approved is None:
        return ResumeEntry(interrupt_id=interrupt.id, status="cancelled")
    return ResumeEntry(
        interrupt_id=interrupt.id, status="resolved", payload={"approved": approved}
    )


def flying_to_london(*texts: str) -> StreamingScriptedModel:
    place = {"place": "London", "lat": 51.5, "lng": -0.12}
    return calling([tool_call("fly_to", place)], *texts)


class BlockingModel(BaseChatModel):
    started: Any = Field(default_factory=asyncio.Event)
    release: Any = Field(default_factory=asyncio.Event)

    @property
    def _llm_type(self) -> str:
        return "blocking"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self

    def _generate(self, *args: Any, **kwargs: Any) -> ChatResult:
        raise NotImplementedError

    async def _agenerate(self, *args: Any, **kwargs: Any) -> ChatResult:
        self.started.set()
        await self.release.wait()
        message = AIMessage(content="finally")
        return ChatResult(generations=[ChatGeneration(message=message)])


class PartialModel(BaseChatModel):
    chunks: list[str]
    then_fail: bool = False

    @property
    def _llm_type(self) -> str:
        return "partial"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self

    def _generate(self, *args: Any, **kwargs: Any) -> ChatResult:
        raise NotImplementedError

    async def _astream(
        self, *args: Any, **kwargs: Any
    ) -> AsyncIterator[ChatGenerationChunk]:
        for chunk in self.chunks:
            yield ChatGenerationChunk(message=AIMessageChunk(content=chunk))
        if self.then_fail:
            raise RuntimeError(PROVIDER_ERROR)
        await asyncio.Event().wait()


class RecordingModel(BaseChatModel):
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "recording"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Self:
        return self

    def _answer(self, messages: list[BaseMessage]) -> str:
        self.seen.append(list(messages))
        asked = next(
            m.content for m in reversed(messages) if isinstance(m, HumanMessage)
        )
        return f"echo: {asked}"

    def _generate(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> ChatResult:
        message = AIMessage(content=self._answer(messages))
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> Iterator[ChatGenerationChunk]:
        prefix, _, asked = self._answer(messages).partition(" ")
        for token in (f"{prefix} ", asked):
            yield ChatGenerationChunk(message=AIMessageChunk(content=token))


@contextmanager
def runtime_using(model: BaseChatModel | None) -> Generator[AgentRuntime]:
    saver = InMemorySaver()
    runtime = AgentRuntime(
        checkpointer=saver,
        agent=agent_factory.build_agent(model, saver) if model else None,
    )
    outer = app.dependency_overrides.get(get_runtime)
    app.dependency_overrides[get_runtime] = lambda: runtime
    try:
        yield runtime
    finally:
        if outer is None:
            del app.dependency_overrides[get_runtime]
        else:
            app.dependency_overrides[get_runtime] = outer
