import asyncio
import uuid

import pytest
from ag_ui.core import EventType
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import SecretStr

from app.core import chat
from app.core.config import settings
from tests.utils.chat import client_input, replying


def turn(text: str, conversation: uuid.UUID) -> chat.RunAgentInput:
    return chat.build_run_input(
        client_input(messages=[{"id": "m1", "role": "user", "content": text}]),
        conversation,
    )


async def say(agent: chat.LangGraphAgent, text: str, conversation: uuid.UUID) -> None:
    events = [e async for e in chat.stream_events(agent, turn(text, conversation))]
    assert events[-1].type == EventType.RUN_FINISHED


def test_the_database_url_is_given_to_psycopg_without_the_sqlalchemy_driver() -> None:
    assert chat.conninfo().startswith("postgresql://")
    assert "+psycopg" not in chat.conninfo()


def test_the_openai_model_is_bounded_and_keeps_nothing_at_the_provider() -> None:
    model = chat.build_model(SecretStr("sk-test-key"), "gpt-test")

    assert model.model_name == "gpt-test"
    assert model.max_tokens == chat.MAX_OUTPUT_TOKENS
    assert model.max_retries == chat.MODEL_MAX_RETRIES
    assert model.request_timeout == chat.MODEL_TIMEOUT_SECONDS
    assert model.store is False
    assert model.use_responses_api is False
    assert "sk-test-key" not in repr(model)


def test_the_chat_is_not_configured_without_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    app = FastAPI()

    async def open_chat() -> chat.Chat:
        async with chat.chat_lifespan(app):
            return app.state.chat

    result = asyncio.run(open_chat())

    assert result.agent is None
    assert isinstance(result.checkpointer, AsyncPostgresSaver)


def test_the_chat_is_configured_with_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", SecretStr("sk-test-key"))
    app = FastAPI()

    async def open_chat() -> chat.Chat:
        async with chat.chat_lifespan(app):
            return app.state.chat

    assert asyncio.run(open_chat()).agent is not None


def test_conversations_persist_in_postgres_stay_apart_and_can_be_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    mine, theirs = uuid.uuid4(), uuid.uuid4()
    app = FastAPI()

    async def scenario() -> tuple[list[str], list[str], list[str], list[str]]:
        async with chat.chat_lifespan(app):
            saver = app.state.chat.checkpointer
            agent = chat.build_agent(
                replying("answer one", "answer two", "answer three"), saver
            )
            await say(agent, "first", mine)
            await say(agent, "second", mine)
            await say(agent, "private", theirs)
            mine_before = [m.content for m in await chat.read_history(agent, mine)]
            theirs_before = [m.content for m in await chat.read_history(agent, theirs)]
            await chat.delete_threads(saver, [mine])
            mine_after = [m.content for m in await chat.read_history(agent, mine)]
            theirs_after = [m.content for m in await chat.read_history(agent, theirs)]
            await chat.delete_threads(saver, [theirs])
            return mine_before, theirs_before, mine_after, theirs_after

    mine_before, theirs_before, mine_after, theirs_after = asyncio.run(scenario())

    assert mine_before == ["first", "answer one", "second", "answer two"]
    assert theirs_before == ["private", "answer three"]
    assert mine_after == []
    assert theirs_after == theirs_before
