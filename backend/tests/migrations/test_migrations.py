import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.core.config import settings

BACKEND = Path(__file__).parents[2]
BEFORE_FULL_NAME_REQUIRED = "fe56fa70289e"
FULL_NAME_REQUIRED = "a28bd8db53bb"
ITEM_INDEXED = "6b3f593b41ce"
ITEM_INDEX = "ix_item_owner_id_created_at"


@pytest.fixture
def migration_db() -> Generator[str]:
    base = make_url(str(settings.DATABASE_URL))
    name = f"migrations_{uuid.uuid4().hex[:12]}"
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
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
