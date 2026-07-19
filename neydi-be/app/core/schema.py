"""Lightweight schema patches for local/dev Postgres volumes.

SQLAlchemy create_all creates new tables but does not alter existing ones.
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from app.core.database import Base


def _add_decks_source_deck_id(connection: Connection) -> None:
    inspector = inspect(connection)
    if "decks" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("decks")}
    if "source_deck_id" in columns:
        return

    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(
            text(
                "ALTER TABLE decks ADD COLUMN source_deck_id UUID "
                "REFERENCES decks(id) ON DELETE SET NULL"
            )
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_decks_source_deck_id ON decks(source_deck_id)")
        )
    elif dialect == "sqlite":
        connection.execute(text("ALTER TABLE decks ADD COLUMN source_deck_id BLOB"))
    else:
        raise RuntimeError(f"Unsupported database dialect for schema patch: {dialect}")

    print("OK Applied schema patch: decks.source_deck_id")


def apply_schema_patches(connection: Connection) -> None:
    _add_decks_source_deck_id(connection)


async def ensure_schema(connection) -> None:
    """Create missing tables and apply incremental column patches."""
    await connection.run_sync(Base.metadata.create_all)
    await connection.run_sync(apply_schema_patches)
