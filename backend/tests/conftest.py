import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.chat_setup import setup as setup_chat_tables
from app.core.chat import Chat
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import AuthThrottle, Item, User
from tests.utils.chat import RecordingModel, chat_using
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import EMAIL_TEST_USER, get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def no_real_model() -> Generator[None]:
    key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = None
    yield
    settings.OPENAI_API_KEY = key


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    """Provide the test database session."""
    asyncio.run(setup_chat_tables())
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.execute(delete(AuthThrottle))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(client=client, email=EMAIL_TEST_USER, db=db)


@pytest.fixture
def chat_model() -> RecordingModel:
    return RecordingModel()


@pytest.fixture
def fake_chat(chat_model: RecordingModel) -> Generator[Chat]:
    with chat_using(chat_model) as chat:
        yield chat
