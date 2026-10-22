from fastapi.encoders import jsonable_encoder
from sqlmodel.ext.asyncio.session import AsyncSession

from src.users import service as users_service
from src.users.models import User
from src.users.schemas import UserCreate
from tests.utils.utils import random_email, random_lower_string


async def test_create_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, full_name=random_lower_string(), password=password
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


async def test_check_if_user_is_active(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, full_name=random_lower_string(), password=password
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    assert user.is_active is True


async def test_check_if_user_is_active_inactive(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, full_name=random_lower_string(), password=password, is_active=False
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    assert user.is_active is False


async def test_check_if_user_is_superuser(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email,
        full_name=random_lower_string(),
        password=password,
        is_superuser=True,
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    assert user.is_superuser is True


async def test_check_if_user_is_superuser_normal_user(db: AsyncSession) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=username, full_name=random_lower_string(), password=password
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False


async def test_get_user(db: AsyncSession) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(
        email=username,
        full_name=random_lower_string(),
        password=password,
        is_superuser=True,
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    user_2 = await db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)
