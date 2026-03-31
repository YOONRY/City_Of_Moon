from __future__ import annotations

from pathlib import Path
import sqlite3

from .database import connect_database, initialize_database
from .models import CardCategory, CardDefinition, CardInstance, Event


def _load_grouped_values(
    connection: sqlite3.Connection,
    table_name: str,
    owner_column: str,
    value_column: str,
) -> dict[str, tuple[str, ...]]:
    query = (
        f"SELECT {owner_column} AS owner_id, {value_column} AS value "
        f"FROM {table_name} ORDER BY {owner_column}, sort_order"
    )
    grouped: dict[str, list[str]] = {}
    for row in connection.execute(query):
        grouped.setdefault(row["owner_id"], []).append(row["value"])
    return {owner_id: tuple(values) for owner_id, values in grouped.items()}


def build_starter_collection(db_path: str | Path | None = None) -> dict[str, CardInstance]:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                instance_id,
                card_id,
                power_bonus,
                current_durability,
                nickname,
                equipped_to_instance_id
            FROM starter_card_instances
            ORDER BY sort_order
            """
        ).fetchall()
    return {
        row["instance_id"]: CardInstance(
            instance_id=row["instance_id"],
            card_id=row["card_id"],
            power_bonus=row["power_bonus"],
            current_durability=row["current_durability"],
            nickname=row["nickname"],
            equipped_to_instance_id=row["equipped_to_instance_id"],
        )
        for row in rows
    }


def build_card_catalog(db_path: str | Path | None = None) -> dict[str, CardDefinition]:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        tag_map = _load_grouped_values(connection, "card_tags", "card_id", "tag")
        rows = connection.execute(
            """
            SELECT
                id,
                name,
                category,
                description,
                power,
                max_durability,
                rarity
            FROM cards
            ORDER BY name
            """
        ).fetchall()
    return {
        row["id"]: CardDefinition(
            id=row["id"],
            name=row["name"],
            category=CardCategory(row["category"]),
            tags=tag_map.get(row["id"], ()),
            description=row["description"],
            power=row["power"],
            max_durability=row["max_durability"],
            rarity=row["rarity"],
        )
        for row in rows
    }


def build_story_events(db_path: str | Path | None = None) -> list[Event]:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        required_tag_map = _load_grouped_values(
            connection,
            "event_required_tags",
            "event_id",
            "tag",
        )
        bonus_tag_map = _load_grouped_values(
            connection,
            "event_bonus_tags",
            "event_id",
            "tag",
        )
        reward_map = _load_grouped_values(
            connection,
            "event_rewards",
            "event_id",
            "card_id",
        )
        required_card_map = _load_grouped_values(
            connection,
            "event_required_cards",
            "event_id",
            "card_id",
        )
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                description,
                success_delta,
                failure_delta,
                success_text,
                failure_text
            FROM events
            ORDER BY sort_order
            """
        ).fetchall()
    return [
        Event(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            required_tags=required_tag_map.get(row["id"], ()),
            required_card_ids=required_card_map.get(row["id"], ()),
            bonus_tags=bonus_tag_map.get(row["id"], ()),
            reward_card_ids=reward_map.get(row["id"], ()),
            success_delta=row["success_delta"],
            failure_delta=row["failure_delta"],
            success_text=row["success_text"],
            failure_text=row["failure_text"],
        )
        for row in rows
    ]
