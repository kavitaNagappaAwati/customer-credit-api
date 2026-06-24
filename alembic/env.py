"""
alembic/env.py
──────────────
Alembic environment script — runs on every `alembic` CLI command.

Key behaviours:
  • Reads DATABASE_URL from the .env file via app.config.settings.
  • Sets `target_metadata` to our SQLAlchemy Base so Alembic can auto-detect
    model changes for `alembic revision --autogenerate`.
  • Supports both offline (SQL-script) and online (live DB connection) modes.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the project root is on sys.path so `from app ...` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database import Base

# ── Alembic Config object ──────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the value from our settings (respects .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that Alembic uses to autogenerate migrations
target_metadata = Base.metadata


# ── Offline migration ─────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode — emits raw SQL to stdout/file
    without requiring a live database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migration ──────────────────────────────────────────────────────────

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode — connects to the live database and
    applies changes directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
