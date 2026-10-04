from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from app.api.deps import SessionDep, error_responses

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check", responses=error_responses(503))
def health_check(session: SessionDep) -> bool:
    """Report whether the API can serve requests."""
    try:
        session.exec(select(1))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return True
