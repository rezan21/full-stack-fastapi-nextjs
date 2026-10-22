import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config

assert config.config_file_name is not None
fileConfig(config.config_file_name, disable_existing_loggers=False)

from sqlmodel import SQLModel

from src.auth import models as auth_models  # noqa
from src.chat import models as chat_models  # noqa
from src.config import settings  # noqa
from src.items import models as items_models  # noqa
from src.users import models as users_models  # noqa

target_metadata = SQLModel.metadata

CHECKPOINT_TABLES = {
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoint_migrations",
}


def include_object(object, name, type_, reflected, compare_to):
    """Leave the tables the chat checkpointer manages out of autogenerate."""
    table = object if type_ == "table" else getattr(object, "table", None)
    return getattr(table, "name", None) not in CHECKPOINT_TABLES


def get_url():
    """Return the configured database URL."""
    return config.get_main_option("sqlalchemy.url") or str(settings.DATABASE_URL)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    """Run migrations on a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in 'online' mode over an async engine."""
    configuration = config.get_section(config.config_ini_section)
    assert configuration is not None
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
