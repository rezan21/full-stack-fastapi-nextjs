"""Creates the first superuser when it is missing."""

import asyncio
import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import SessionFactory
from src.users import service as users_service
from src.users.config import users_settings
from src.users.models import User
from src.users.schemas import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    """Create the initial data if missing."""
    user = (
        await session.exec(
            select(User).where(User.email == users_settings.FIRST_SUPERUSER.lower())
        )
    ).first()
    if not user:
        user_in = UserCreate(
            email=users_settings.FIRST_SUPERUSER,
            password=users_settings.FIRST_SUPERUSER_PASSWORD,
            full_name=users_settings.FIRST_SUPERUSER,
            is_superuser=True,
        )
        user = await users_service.create_user(session=session, user_create=user_in)


async def init() -> None:
    """Create the initial data."""
    async with SessionFactory() as session:
        await init_db(session)


def main() -> None:
    """Entry point for creating the initial data."""
    logger.info("Creating initial data")
    asyncio.run(init())
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
