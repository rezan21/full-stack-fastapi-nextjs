from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from src.config import settings
from src.database import get_db
from src.main import app


async def test_health_check_reports_the_database_is_reachable(
    client: AsyncClient,
) -> None:
    r = await client.get(f"{settings.API_V1_STR}/utils/health-check")

    assert r.status_code == 200
    assert r.json() is True


async def test_health_check_fails_when_the_database_is_unreachable(
    client: AsyncClient,
) -> None:
    class UnreachableSession:
        def exec(self, *_args: object) -> None:
            raise OperationalError("select 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_db] = lambda: UnreachableSession()
    try:
        r = await client.get(f"{settings.API_V1_STR}/utils/health-check")
    finally:
        del app.dependency_overrides[get_db]

    assert r.status_code == 503
    assert r.json() == {"detail": "Database unavailable"}
