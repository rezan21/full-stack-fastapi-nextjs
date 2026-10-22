import pytest
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.main import build_app

DOC_PATHS = ["/docs", "/redoc", f"{settings.API_V1_STR}/openapi.json"]


def client_for(*, docs: bool) -> AsyncClient:
    transport = ASGITransport(app=build_app(docs=docs))
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.parametrize("path", DOC_PATHS)
async def test_the_docs_are_served_when_enabled(path: str) -> None:
    async with client_for(docs=True) as client:
        assert (await client.get(path)).status_code == 200


@pytest.mark.parametrize("path", DOC_PATHS)
async def test_the_docs_are_not_served_when_disabled(path: str) -> None:
    async with client_for(docs=False) as client:
        assert (await client.get(path)).status_code == 404


async def test_the_api_still_answers_when_the_docs_are_disabled() -> None:
    async with client_for(docs=False) as client:
        response = await client.get(f"{settings.API_V1_STR}/utils/health-check")

    assert response.status_code == 200
