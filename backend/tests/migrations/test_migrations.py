import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.core.config import settings

BACKEND = Path(__file__).parents[2]
BEFORE_FULL_NAME_REQUIRED = "fe56fa70289e"
FULL_NAME_REQUIRED = "a28bd8db53bb"
ITEM_INDEXED = "6b3f593b41ce"
ITEM_INDEX = "ix_item_owner_id_created_at"
TOKEN_VERSIONED = "be73c5442ef9"
EMAILS_LOWERED = "9f3cbb8a0df2"
CREATED_AT_REQUIRED = "165d280e56b9"


@pytest.fixture
def migration_db() -> Generator[str]:
    base = make_url(str(settings.DATABASE_URL))
    name = f"migrations_{uuid.uuid4().hex[:12]}"
    admin = create_engine(
        base.set(
            username="postgres",
            password=dotenv_values(BACKEND / ".env")["POSTGRES_PASSWORD"],
            database="postgres",
        ),
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}" OWNER "{base.username}"'))
    try:
        yield base.set(database=name).render_as_string(hide_password=False)
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "app" / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def full_name_is_nullable(url: str) -> bool:
    engine = create_engine(url)
    with engine.connect() as connection:
        nullable = connection.execute(
            text(
                "select is_nullable from information_schema.columns "
                "where table_name = 'user' and column_name = 'full_name'"
            )
        ).scalar_one()
    engine.dispose()
    return str(nullable) == "YES"


def item_index_columns(url: str) -> list[str]:
    engine = create_engine(url)
    with engine.connect() as connection:
        columns = connection.execute(
            text(
                "select a.attname from pg_index i "
                "join pg_class c on c.oid = i.indexrelid "
                "join pg_attribute a on a.attrelid = i.indrelid "
                "and a.attnum = any(i.indkey) "
                "where c.relname = :name "
                "order by array_position(i.indkey, a.attnum)"
            ),
            {"name": ITEM_INDEX},
        ).scalars()
        result = list(columns)
    engine.dispose()
    return result


def test_migrations_produce_the_schema_the_models_declare(migration_db: str) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, "head")
    command.check(config)


def test_full_name_migration_backfills_missing_names(migration_db: str) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, BEFORE_FULL_NAME_REQUIRED)
    users = {
        "null@example.com": None,
        "empty@example.com": "",
        "blank@example.com": "   ",
        "named@example.com": "Real Name",
    }
    engine = create_engine(migration_db)
    with engine.begin() as connection:
        for email, full_name in users.items():
            connection.execute(
                text(
                    'insert into "user" (id, email, hashed_password, is_active, '
                    "is_superuser, full_name) values (:id, :email, 'x', true, false, "
                    ":full_name)"
                ),
                {"id": uuid.uuid4(), "email": email, "full_name": full_name},
            )

    command.upgrade(config, FULL_NAME_REQUIRED)

    with engine.connect() as connection:
        rows = connection.execute(text('select email, full_name from "user"'))
        names = {row.email: row.full_name for row in rows}
    assert names == {
        "null@example.com": "null@example.com",
        "empty@example.com": "empty@example.com",
        "blank@example.com": "blank@example.com",
        "named@example.com": "Real Name",
    }
    assert not full_name_is_nullable(migration_db)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                'insert into "user" (id, email, hashed_password, is_active, '
                "is_superuser, full_name) values (:id, 'late@example.com', 'x', true, "
                "false, null)"
            ),
            {"id": uuid.uuid4()},
        )
    engine.dispose()

    command.downgrade(config, BEFORE_FULL_NAME_REQUIRED)
    assert full_name_is_nullable(migration_db)


def test_item_index_is_created_and_dropped(migration_db: str) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, ITEM_INDEXED)
    assert item_index_columns(migration_db) == ["owner_id", "created_at"]

    command.downgrade(config, FULL_NAME_REQUIRED)
    assert item_index_columns(migration_db) == []


def insert_users(url: str, emails: list[str]) -> None:
    engine = create_engine(url)
    with engine.begin() as connection:
        for email in emails:
            connection.execute(
                text(
                    'insert into "user" (id, email, hashed_password, is_active, '
                    "is_superuser, full_name) values (:id, :email, 'x', true, false, "
                    "'Name')"
                ),
                {"id": uuid.uuid4(), "email": email},
            )
    engine.dispose()


def stored_emails(url: str) -> set[str]:
    engine = create_engine(url)
    with engine.connect() as connection:
        emails = set(connection.execute(text('select email from "user"')).scalars())
    engine.dispose()
    return emails


def token_versions(url: str) -> list[int]:
    engine = create_engine(url)
    with engine.connect() as connection:
        versions = list(
            connection.execute(text('select token_version from "user"')).scalars()
        )
    engine.dispose()
    return versions


def test_token_version_starts_at_zero_for_existing_users_and_is_dropped(
    migration_db: str,
) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, ITEM_INDEXED)
    insert_users(migration_db, ["existing@example.com"])

    command.upgrade(config, TOKEN_VERSIONED)
    assert token_versions(migration_db) == [0]

    command.downgrade(config, ITEM_INDEXED)
    with pytest.raises(Exception, match="token_version"):
        token_versions(migration_db)


def test_emails_are_lowercased(migration_db: str) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, TOKEN_VERSIONED)
    insert_users(migration_db, ["Mixed@Example.com", "lower@example.com"])

    command.upgrade(config, EMAILS_LOWERED)

    assert stored_emails(migration_db) == {"mixed@example.com", "lower@example.com"}


def test_lowercasing_refuses_addresses_that_differ_only_by_case(
    migration_db: str,
) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, TOKEN_VERSIONED)
    insert_users(migration_db, ["Clash@Example.com", "clash@example.com"])

    with pytest.raises(RuntimeError, match="differ only by case"):
        command.upgrade(config, EMAILS_LOWERED)

    assert stored_emails(migration_db) == {"Clash@Example.com", "clash@example.com"}


def created_at_values(url: str, table: str) -> list[object]:
    engine = create_engine(url)
    with engine.connect() as connection:
        values = list(
            connection.execute(text(f'select created_at from "{table}"')).scalars()
        )
    engine.dispose()
    return values


def created_at_is_nullable(url: str, table: str) -> bool:
    engine = create_engine(url)
    with engine.connect() as connection:
        nullable = connection.execute(
            text(
                "select is_nullable from information_schema.columns "
                "where table_name = :table and column_name = 'created_at'"
            ),
            {"table": table},
        ).scalar_one()
    engine.dispose()
    return str(nullable) == "YES"


def test_created_at_is_backfilled_and_required(migration_db: str) -> None:
    config = alembic_config(migration_db)
    command.upgrade(config, EMAILS_LOWERED)
    insert_users(migration_db, ["old@example.com"])
    engine = create_engine(migration_db)
    with engine.begin() as connection:
        owner = connection.execute(text('select id from "user"')).scalar_one()
        connection.execute(
            text("insert into item (id, title, owner_id) values (:id, 'Old', :owner)"),
            {"id": uuid.uuid4(), "owner": owner},
        )
    engine.dispose()
    assert created_at_values(migration_db, "user") == [None]
    assert created_at_values(migration_db, "item") == [None]

    command.upgrade(config, CREATED_AT_REQUIRED)

    for table in ("user", "item"):
        assert None not in created_at_values(migration_db, table)
        assert not created_at_is_nullable(migration_db, table)

    command.downgrade(config, EMAILS_LOWERED)
    for table in ("user", "item"):
        assert created_at_is_nullable(migration_db, table)
