import uuid

import pytest
from ag_ui.core import EventType
from ag_ui_langgraph import LangGraphAgent
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import SecretStr

from src.agent import factory as agent_factory
from src.agent import runtime as agent_runtime
from src.agent import streaming as agent_streaming
from src.agent import threads as agent_threads
from src.agent.config import agent_settings
from src.main import app
from tests.utils.agent import CONTEXT, replying, run_input


async def say(agent: LangGraphAgent, text: str, thread_id: str) -> None:
    events = [
        e
        async for e in agent_streaming.stream_events(
            agent, run_input(text, thread_id), CONTEXT
        )
    ]
    assert events[-1].type == EventType.RUN_FINISHED


def test_the_database_url_is_given_to_psycopg_without_the_sqlalchemy_driver() -> None:
    assert agent_runtime.conninfo().startswith("postgresql://")
    assert "+psycopg" not in agent_runtime.conninfo()


def test_the_openai_model_is_bounded_and_keeps_nothing_at_the_provider() -> None:
    model = agent_factory.build_model(SecretStr("sk-test-key"), "gpt-test")

    assert model.model_name == "gpt-test"
    assert model.max_tokens == agent_factory.MAX_OUTPUT_TOKENS
    assert model.max_retries == agent_factory.MODEL_MAX_RETRIES
    assert model.request_timeout == agent_factory.MODEL_TIMEOUT_SECONDS
    assert model.store is False
    assert model.use_responses_api is False
    assert "sk-test-key" not in repr(model)


def test_the_openai_model_calls_one_tool_at_a_time() -> None:
    model = agent_factory.build_model(SecretStr("sk-test-key"), "gpt-test")

    assert model.model_kwargs == {"parallel_tool_calls": False}


async def test_the_agent_is_not_configured_without_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_settings, "OPENAI_API_KEY", None)
    app = FastAPI()

    async def open_runtime() -> agent_runtime.AgentRuntime:
        async with agent_runtime.lifespan(app):
            return app.state.agent_runtime

    result = await open_runtime()

    assert result.agent is None
    assert isinstance(result.checkpointer, AsyncPostgresSaver)


async def test_the_agent_is_configured_with_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_settings, "OPENAI_API_KEY", SecretStr("sk-test-key"))
    app = FastAPI()

    async def open_runtime() -> agent_runtime.AgentRuntime:
        async with agent_runtime.lifespan(app):
            return app.state.agent_runtime

    assert (await open_runtime()).agent is not None


async def test_threads_persist_in_postgres_stay_apart_and_can_be_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_settings, "OPENAI_API_KEY", None)
    mine, theirs = str(uuid.uuid4()), str(uuid.uuid4())
    app = FastAPI()

    async def scenario() -> tuple[list[str], list[str], list[str], list[str]]:
        async with agent_runtime.lifespan(app):
            saver = app.state.agent_runtime.checkpointer
            agent = agent_factory.build_agent(
                replying("answer one", "answer two", "answer three"), saver
            )
            await say(agent, "first", mine)
            await say(agent, "second", mine)
            await say(agent, "private", theirs)
            mine_before = [
                m.content for m in await agent_threads.read_history(agent, mine)
            ]
            theirs_before = [
                m.content for m in await agent_threads.read_history(agent, theirs)
            ]
            await agent_threads.delete_threads(saver, [mine])
            mine_after = [
                m.content for m in await agent_threads.read_history(agent, mine)
            ]
            theirs_after = [
                m.content for m in await agent_threads.read_history(agent, theirs)
            ]
            await agent_threads.delete_threads(saver, [theirs])
            return mine_before, theirs_before, mine_after, theirs_after

    mine_before, theirs_before, mine_after, theirs_after = await scenario()

    assert mine_before == ["first", "answer one", "second", "answer two"]
    assert theirs_before == ["private", "answer three"]
    assert mine_after == []
    assert theirs_after == theirs_before


@pytest.mark.usefixtures("client")
def test_the_test_suite_never_builds_the_real_model() -> None:
    assert app.state.agent_runtime.agent is None
