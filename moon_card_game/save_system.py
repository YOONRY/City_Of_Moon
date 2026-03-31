from __future__ import annotations

import ast
from pathlib import Path
from random import Random

from .content import build_card_catalog, build_story_events
from .database import connect_database, initialize_database
from .game import GameState
from .models import CardInstance

DEFAULT_SAVE_SLOT = "main"


def has_saved_game(
    db_path: str | Path | None = None,
    slot_name: str = DEFAULT_SAVE_SLOT,
) -> bool:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM save_slots WHERE slot_name = ?",
            (slot_name,),
        ).fetchone()
    return row is not None


def save_game_state(
    game: GameState,
    db_path: str | Path | None = None,
    slot_name: str = DEFAULT_SAVE_SLOT,
) -> None:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        try:
            connection.execute(
                """
                INSERT INTO save_slots (
                    slot_name,
                    stability,
                    completed_events,
                    rng_state,
                    saved_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slot_name) DO UPDATE SET
                    stability = excluded.stability,
                    completed_events = excluded.completed_events,
                    rng_state = excluded.rng_state,
                    saved_at = CURRENT_TIMESTAMP
                """,
                (
                    slot_name,
                    game.stability,
                    game.completed_events,
                    repr(game.rng.getstate()),
                ),
            )
            connection.execute("DELETE FROM save_piles WHERE slot_name = ?", (slot_name,))
            connection.execute("DELETE FROM save_events WHERE slot_name = ?", (slot_name,))
            connection.execute(
                "DELETE FROM save_card_instances WHERE slot_name = ?",
                (slot_name,),
            )

            connection.executemany(
                """
                INSERT INTO save_card_instances (
                    slot_name,
                    instance_id,
                    card_id,
                    power_bonus,
                    current_durability,
                    nickname,
                    equipped_to_instance_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        slot_name,
                        card_instance.instance_id,
                        card_instance.card_id,
                        card_instance.power_bonus,
                        card_instance.current_durability,
                        card_instance.nickname,
                        card_instance.equipped_to_instance_id,
                    )
                    for card_instance in sorted(
                        game.collection.values(),
                        key=lambda item: item.instance_id,
                    )
                ],
            )
            connection.executemany(
                """
                INSERT INTO save_events (slot_name, sort_order, event_id)
                VALUES (?, ?, ?)
                """,
                [
                    (slot_name, index, event.id)
                    for index, event in enumerate(game.events, start=1)
                ],
            )

            pile_rows: list[tuple[str, str, int, str]] = []
            for pile_name, pile in (
                ("hand", game.hand),
                ("draw", game.draw_pile),
                ("discard", game.discard_pile),
            ):
                pile_rows.extend(
                    (slot_name, pile_name, index, instance_id)
                    for index, instance_id in enumerate(pile, start=1)
                )
            if pile_rows:
                connection.executemany(
                    """
                    INSERT INTO save_piles (
                        slot_name,
                        pile_name,
                        sort_order,
                        instance_id
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    pile_rows,
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def load_game_state(
    db_path: str | Path | None = None,
    slot_name: str = DEFAULT_SAVE_SLOT,
) -> GameState | None:
    initialize_database(db_path)
    with connect_database(db_path) as connection:
        save_row = connection.execute(
            """
            SELECT stability, completed_events, rng_state
            FROM save_slots
            WHERE slot_name = ?
            """,
            (slot_name,),
        ).fetchone()
        if save_row is None:
            return None

        card_rows = connection.execute(
            """
            SELECT
                instance_id,
                card_id,
                power_bonus,
                current_durability,
                nickname,
                equipped_to_instance_id
            FROM save_card_instances
            WHERE slot_name = ?
            ORDER BY instance_id
            """,
            (slot_name,),
        ).fetchall()
        event_rows = connection.execute(
            """
            SELECT event_id
            FROM save_events
            WHERE slot_name = ?
            ORDER BY sort_order
            """,
            (slot_name,),
        ).fetchall()
        pile_rows = connection.execute(
            """
            SELECT pile_name, instance_id
            FROM save_piles
            WHERE slot_name = ?
            ORDER BY pile_name, sort_order
            """,
            (slot_name,),
        ).fetchall()

    catalog = build_card_catalog(db_path)
    event_map = {event.id: event for event in build_story_events(db_path)}
    remaining_events = []
    for row in event_rows:
        event = event_map.get(row["event_id"])
        if event is None:
            raise ValueError(f"Saved event '{row['event_id']}' is not defined in the database.")
        remaining_events.append(event)

    collection = {
        row["instance_id"]: CardInstance(
            instance_id=row["instance_id"],
            card_id=row["card_id"],
            power_bonus=row["power_bonus"],
            current_durability=row["current_durability"],
            nickname=row["nickname"],
            equipped_to_instance_id=row["equipped_to_instance_id"],
        )
        for row in card_rows
    }

    piles = {"hand": [], "draw": [], "discard": []}
    for row in pile_rows:
        instance_id = row["instance_id"]
        if instance_id not in collection:
            raise ValueError(f"Saved pile references missing instance '{instance_id}'.")
        piles[row["pile_name"]].append(instance_id)

    rng = Random()
    rng.setstate(ast.literal_eval(save_row["rng_state"]))

    return GameState(
        catalog=catalog,
        events=remaining_events,
        collection=collection,
        rng=rng,
        stability=save_row["stability"],
        draw_pile=piles["draw"],
        discard_pile=piles["discard"],
        hand=piles["hand"],
        completed_events=save_row["completed_events"],
        auto_draw_on_init=False,
    )
