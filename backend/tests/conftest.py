from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import AuthThrottle
from src.chat.client import Chat
from src.chat.config import chat_settings
from src.database import SessionFactory, engine
from src.items.models import Item
from src.main import app
from src.scripts.chat_setup import setup as setup_chat_tables
from src.scripts.initial_data import init_db
from src.users.models import User
from tests.utils.chat import RecordingModel, chat_using
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import EMAIL_TEST_USER, get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def no_real_model() -> Generator[None]:
    key = chat_settings.OPENAI_API_KEY
    chat_settings.OPENAI_API_KEY = None
    yield
    chat_settings.OPENAI_API_KEY = key


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncGenerator[None]:
    """Prepare the test database and clear what the tests added."""
    await setup_chat_tables()
    async with SessionFactory() as session:
        await init_db(session)
    yield
    async with SessionFactory() as session:
        await session.exec(delete(Item))
        await session.exec(delete(User))
        await session.exec(delete(AuthThrottle))
        await session.commit()
    await engine.dispose()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Provide a database session."""
    async with SessionFactory() as session:
        yield session


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test", follow_redirects=True
        ) as ac:
            yield ac


@pytest.fixture(scope="module")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    return await get_superuser_token_headers(client)


@pytest.fixture(scope="module")
async def normal_user_token_headers(client: AsyncClient) -> dict[str, str]:
    async with SessionFactory() as session:
        return await authentication_token_from_email(
            client=client, email=EMAIL_TEST_USER, db=session
        )


@pytest.fixture
def chat_model() -> RecordingModel:
    return RecordingModel()


@pytest.fixture
def fake_chat(chat_model: RecordingModel) -> Generator[Chat]:
    with chat_using(chat_model) as chat:
        yield chat
