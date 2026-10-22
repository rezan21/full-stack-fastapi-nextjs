from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.health.exceptions import DatabaseUnavailable


async def check_database(session: AsyncSession) -> None:
    """Raise unless the database answers."""
    try:
        await session.exec(select(1))
    except SQLAlchemyError:
        raise DatabaseUnavailable()
