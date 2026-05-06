"""
Alembic environment configuration.
Connect alembic to the app's settings and base so 
1. it can connect to the right DB (settings.database_url)
2. know what tables models declared in this app (from Base.metadata)
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

#app's settings + models, makes Alembic aware of every model that inherits from Base.
from config import settings
from db.database import Base #Base.metadata empty for now

#import booking model so its registered in Base.metadata for the migration
from models.booking import Booking  # noqa: F401
from models.user import User # noqa: F401

#alembic config
config = context.config

#override the sqlalchemy.url from alembic.ini with our settings
config.set_main_option("sqlalchemy.url", settings.database_url)

#set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

#target_metadata (new DB model) is what "--autogenerate" compares againts existing DB.
target_metadata = Base.metadata #the diff between new and existing DB is called migration files


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL scripts without a DB connection.
    Rarely used; we run online."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Detect column type changes (e.g. VARCHAR(50) -> VARCHAR(100))
        compare_type=True,
        # Detect server-default changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Connect to DB asynchronously, then run migrations synchronously inside."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pooling — Alembic runs once and exits
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Async entry point — what Alembic actually calls."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()