import asyncio
import os

from src.database import SessionFactory
from src.users import service as users_service
from src.users.schemas import UserCreate

ACCOUNTS = (
    ("e2e-admin@example.com", "E2E Admin", True),
    ("e2e-user@example.com", "E2E User", False),
)


async def seed() -> None:
    password = os.environ["E2E_PASSWORD"]
    async with SessionFactory() as session:
        for email, full_name, is_superuser in ACCOUNTS:
            if await users_service.get_user_by_email(session=session, email=email):
                continue
            await users_service.create_user(
                session=session,
                user_create=UserCreate(
                    email=email,
                    full_name=full_name,
                    password=password,
                    is_superuser=is_superuser,
                ),
            )


asyncio.run(seed())
