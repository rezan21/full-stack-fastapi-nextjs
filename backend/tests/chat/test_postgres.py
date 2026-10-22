import uuid

import pytest
from ag_ui.core import EventType, RunAgentInput
from ag_ui_langgraph import LangGraphAgent
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import SecretStr

from src.chat import client as chat_client
from src.chat import constants as chat_constants
from src.chat import service as chat_service
from src.chat.config import chat_settings
from tests.utils.chat import client_input, replying


def turn(text: str, conversation: uuid.UUID) -> RunAgentInput:
    return chat_service.build_run_input(
        client_input(messages=[{"id": "m1", "role": "user", "content": text}]),
        conversation,
    )


async def say(agent: LangGraphAgent, text: str, conversation: uuid.UUID) -> None:
    events = [
        e async for e in chat_client.stream_events(agent, turn(text, conversation))
    ]
    assert events[-1].type == EventType.RUN_FINISHED


def test_the_database_url_is_given_to_psycopg_without_the_sqlalchemy_driver() -> None:
    assert chat_client.conninfo().startswith("postgresql://")
    assert "+psycopg" not in chat_client.conninfo()


def test_the_openai_model_is_bounded_and_keeps_nothing_at_the_provider() -> None:
    model = chat_client.build_model(SecretStr("sk-test-key"), "gpt-test")

    assert model.model_name == "gpt-test"
    assert model.max_tokens == chat_constants.MAX_OUTPUT_TOKENS
    assert model.max_retries == chat_constants.MODEL_MAX_RETRIES
    assert model.request_timeout == chat_constants.MODEL_TIMEOUT_SECONDS
    assert model.store is False
    assert model.use_responses_api is False
    assert "sk-test-key" not in repr(model)


async def test_the_chat_is_not_configured_without_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_settings, "OPENAI_API_KEY", None)
    app = FastAPI()

    async def open_chat() -> chat_client.Chat:
        async with chat_client.chat_lifespan(app):
            return app.state.chat

    result = await open_chat()

    assert result.agent is None
    assert isinstance(result.checkpointer, AsyncPostgresSaver)


async def test_the_chat_is_configured_with_an_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_settings, "OPENAI_API_KEY", SecretStr("sk-test-key"))
    app = FastAPI()

    async def open_chat() -> chat_client.Chat:
        async with chat_client.chat_lifespan(app):
            return app.state.chat

    assert (await open_chat()).agent is not None


async def test_conversations_persist_in_postgres_stay_apart_and_can_be_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_settings, "OPENAI_API_KEY", None)
    mine, theirs = uuid.uuid4(), uuid.uuid4()
    app = FastAPI()

    async def scenario() -> tuple[list[str], list[str], list[str], list[str]]:
        async with chat_client.chat_lifespan(app):
            saver = app.state.chat.checkpointer
            agent = chat_client.build_agent(
                replying("answer one", "answer two", "answer three"), saver
            )
            await say(agent, "first", mine)
            await say(agent, "second", mine)
            await say(agent, "private", theirs)
            mine_before = [
                m.content for m in await chat_client.read_history(agent, mine)
            ]
            theirs_before = [
                m.content for m in await chat_client.read_history(agent, theirs)
            ]
            await chat_client.delete_threads(saver, [mine])
            mine_after = [
                m.content for m in await chat_client.read_history(agent, mine)
            ]
            theirs_after = [
                m.content for m in await chat_client.read_history(agent, theirs)
            ]
            await chat_client.delete_threads(saver, [theirs])
            return mine_before, theirs_before, mine_after, theirs_after

    mine_before, theirs_before, mine_after, theirs_after = await scenario()

    assert mine_before == ["first", "answer one", "second", "answer two"]
    assert theirs_before == ["private", "answer three"]
    assert mine_after == []
    assert theirs_after == theirs_before
