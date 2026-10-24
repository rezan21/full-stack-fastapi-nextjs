from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.utils import get_password_hash
from src.config import settings
from src.users import service as users_service
from src.users.models import User
from src.users.schemas import UserCreate
from tests.utils.utils import random_email, random_lower_string


async def user_authentication_headers(
    *, client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


async def create_random_user(db: AsyncSession) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, full_name=random_lower_string(), password=password
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    return user


async def create_random_superuser(db: AsyncSession) -> User:
    user = await create_random_user(db)
    user.is_superuser = True
    db.add(user)
    await db.commit()
    return user


async def authentication_token_from_email(
    *, client: AsyncClient, email: str, db: AsyncSession
) -> dict[str, str]:
    """Return authentication headers for the user with the given email."""
    password = random_lower_string()
    user = await users_service.get_user_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(
            email=email, full_name=random_lower_string(), password=password
        )
        user = await users_service.create_user(session=db, user_create=user_in_create)
    else:
        user.hashed_password = get_password_hash(password)
        db.add(user)
        await db.commit()

    return await user_authentication_headers(
        client=client, email=email, password=password
    )
