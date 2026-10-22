from fastapi import APIRouter

from src.database import SessionDep
from src.exceptions import error_responses
from src.health import service as health_service

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check", responses=error_responses(503))
async def health_check(session: SessionDep) -> bool:
    """Report whether the API can serve requests."""
    await health_service.check_database(session)
    return True
