from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DATABASE_FILENAME = "city_of_moon.sqlite3"
CURRENT_SCHEMA_VERSION = 5


def get_default_database_path() -> Path:
    return DATA_DIR / DEFAULT_DATABASE_FILENAME


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def _migrate_existing_data(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "cards"):
        card_columns = _table_columns(connection, "cards")
        if "max_durability" not in card_columns:
            connection.execute(
                "ALTER TABLE cards ADD COLUMN max_durability INTEGER NOT NULL DEFAULT 3"
            )
        for stat_name in ("strength", "agility", "intelligence", "charm"):
            if stat_name not in card_columns:
                connection.execute(
                    f"ALTER TABLE cards ADD COLUMN {stat_name} INTEGER NOT NULL DEFAULT 0"
                )
        if "info_kind" not in card_columns:
            connection.execute(
                "ALTER TABLE cards ADD COLUMN info_kind TEXT NOT NULL DEFAULT ''"
            )

    if _table_exists(connection, "events") and "difficulty" not in _table_columns(
        connection,
        "events",
    ):
        connection.execute(
            "ALTER TABLE events ADD COLUMN difficulty INTEGER NOT NULL DEFAULT 3"
        )

    if not _table_exists(connection, "starter_card_instances"):
        return

    if "equipped_to_instance_id" not in _table_columns(connection, "starter_card_instances"):
        connection.execute(
            "ALTER TABLE starter_card_instances ADD COLUMN equipped_to_instance_id TEXT NOT NULL DEFAULT ''"
        )

    if _table_exists(connection, "save_card_instances") and "equipped_to_instance_id" not in _table_columns(
        connection,
        "save_card_instances",
    ):
        connection.execute(
            "ALTER TABLE save_card_instances ADD COLUMN equipped_to_instance_id TEXT NOT NULL DEFAULT ''"
        )

    starter_instance_count = connection.execute(
        "SELECT COUNT(*) FROM starter_card_instances"
    ).fetchone()[0]
    if starter_instance_count > 0 or not _table_exists(connection, "starter_cards"):
        return

    sort_order = 1
    starter_rows = connection.execute(
        "SELECT card_id, count FROM starter_cards ORDER BY card_id"
    ).fetchall()
    for row in starter_rows:
        max_durability = connection.execute(
            "SELECT max_durability FROM cards WHERE id = ?",
            (row["card_id"],),
        ).fetchone()[0]
        for copy_index in range(1, row["count"] + 1):
            connection.execute(
                """
                INSERT OR IGNORE INTO starter_card_instances (
                    instance_id,
                    sort_order,
                    card_id,
                    power_bonus,
                    current_durability,
                    nickname,
                    equipped_to_instance_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"starter_{row['card_id']}_{copy_index}",
                    sort_order,
                    row["card_id"],
                    0,
                    max_durability,
                    "",
                    "",
                ),
            )
            sort_order += 1


def _apply_content_updates(connection: sqlite3.Connection) -> None:
    updates_path = DATA_DIR / "content_updates_ko.sql"
    if updates_path.exists():
        connection.executescript(updates_path.read_text(encoding="utf-8"))


def initialize_database(db_path: str | Path | None = None) -> Path:
    database_path = Path(db_path) if db_path is not None else get_default_database_path()
    database_path = database_path.expanduser().resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((DATA_DIR / "schema.sql").read_text(encoding="utf-8"))
        _migrate_existing_data(connection)
        card_count = connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        if card_count == 0:
            connection.executescript((DATA_DIR / "seed.sql").read_text(encoding="utf-8"))
        _migrate_existing_data(connection)
        _apply_content_updates(connection)
        connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
        connection.commit()
    finally:
        connection.close()

    return database_path


@contextmanager
def connect_database(db_path: str | Path | None = None):
    database_path = initialize_database(db_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()
