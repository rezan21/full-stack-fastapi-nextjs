import pytest
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import service as auth_service
from src.auth.utils import verify_password
from src.users import service as users_service
from src.users.models import User
from src.users.schemas import UserCreate
from tests.utils.utils import random_email, random_lower_string


async def test_authenticate_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, full_name=random_lower_string(), password=password
    )
    user = await users_service.create_user(session=db, user_create=user_in)
    authenticated_user = await auth_service.authenticate(
        session=db, email=email, password=password
    )
    assert authenticated_user
    assert user.email == authenticated_user.email


async def test_not_authenticate_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user = await auth_service.authenticate(session=db, email=email, password=password)
    assert user is None


async def test_authenticate_unknown_email_still_verifies_a_password_hash(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    verified_hashes: list[str] = []

    def fake_verify_password(
        _plain_password: str, hashed_password: str
    ) -> tuple[bool, str | None]:
        verified_hashes.append(hashed_password)
        return False, None

    monkeypatch.setattr(auth_service, "verify_password", fake_verify_password)

    user = await auth_service.authenticate(
        session=db, email=random_email(), password=random_lower_string()
    )

    assert user is None
    assert verified_hashes == [auth_service.DUMMY_HASH]


async def test_authenticate_user_with_bcrypt_upgrades_to_argon2(
    db: AsyncSession,
) -> None:
    email = random_email()
    password = random_lower_string()

    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")

    user = User(
        email=email, full_name=random_lower_string(), hashed_password=bcrypt_hash
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.hashed_password.startswith("$2")

    authenticated_user = await auth_service.authenticate(
        session=db, email=email, password=password
    )
    assert authenticated_user
    assert authenticated_user.email == email

    await db.refresh(authenticated_user)

    assert authenticated_user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(
        password, authenticated_user.hashed_password
    )
    assert verified
    assert updated_hash is None
