"""
ClauseIQ — Alembic Migration Environment

Configured to use the sync database URL from app.config for migrations,
and imports all ORM models so autogenerate can detect schema changes.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure the backend directory is on sys.path so app imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import Base

# Import all models here so Alembic's autogenerate detects them
from app.models import (  # noqa: F401
    User, Project, Contract, DocumentChunk,
    ExtractedClause, DetectedRisk, ExecutiveSummary,
    ChatMessage, Comparison,
)

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the sync version from our settings
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
