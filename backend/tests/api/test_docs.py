import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import build_app

DOC_PATHS = ["/docs", "/redoc", f"{settings.API_V1_STR}/openapi.json"]


@pytest.mark.parametrize("path", DOC_PATHS)
def test_the_docs_are_served_when_enabled(path: str) -> None:
    assert TestClient(build_app(docs=True)).get(path).status_code == 200


@pytest.mark.parametrize("path", DOC_PATHS)
def test_the_docs_are_not_served_when_disabled(path: str) -> None:
    assert TestClient(build_app(docs=False)).get(path).status_code == 404


def test_the_api_still_answers_when_the_docs_are_disabled() -> None:
    client = TestClient(build_app(docs=False))
    assert client.get(f"{settings.API_V1_STR}/utils/health-check").status_code == 200
