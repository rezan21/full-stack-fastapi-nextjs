from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.core.config import settings
from app.main import app


def test_health_check_reports_the_database_is_reachable(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check")

    assert r.status_code == 200
    assert r.json() is True


def test_health_check_fails_when_the_database_is_unreachable(
    client: TestClient,
) -> None:
    class UnreachableSession:
        def exec(self, *_args: object) -> None:
            raise OperationalError("select 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_db] = lambda: UnreachableSession()
    try:
        r = client.get(f"{settings.API_V1_STR}/utils/health-check")
    finally:
        del app.dependency_overrides[get_db]

    assert r.status_code == 503
    assert r.json() == {"detail": "Database unavailable"}
