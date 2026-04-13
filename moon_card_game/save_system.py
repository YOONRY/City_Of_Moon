from __future__ import annotations

import ast
from pathlib import Path
from random import Random

from .content import build_card_catalog, build_story_events
from .database import connect_database, initialize_database
from .game import GameState
from .models import CardInstance, Event

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
            connection.execute(
                """
                INSERT INTO save_run_state (
                    slot_name,
                    day,
                    actions_remaining,
                    money,
                    special_chain_progress,
                    special_chain_failed,
                    offer_sequence,
                    tavern_visits_today
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slot_name) DO UPDATE SET
                    day = excluded.day,
                    actions_remaining = excluded.actions_remaining,
                    money = excluded.money,
                    special_chain_progress = excluded.special_chain_progress,
                    special_chain_failed = excluded.special_chain_failed,
                    offer_sequence = excluded.offer_sequence,
                    tavern_visits_today = excluded.tavern_visits_today
                """,
                (
                    slot_name,
                    game.day,
                    0,
                    game.money,
                    game.special_chain_progress,
                    int(game.special_chain_failed),
                    game.offer_sequence,
                    game.tavern_visits_today,
                ),
            )
            connection.execute("DELETE FROM save_piles WHERE slot_name = ?", (slot_name,))
            connection.execute("DELETE FROM save_events WHERE slot_name = ?", (slot_name,))
            connection.execute("DELETE FROM save_event_offers WHERE slot_name = ?", (slot_name,))
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
                    equipped_to_instance_id,
                    busy_until_day
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                        card_instance.busy_until_day,
                    )
                    for card_instance in sorted(
                        game.collection.values(),
                        key=lambda item: item.instance_id,
                    )
                ],
            )
            connection.executemany(
                """
                INSERT INTO save_event_offers (
                    slot_name,
                    sort_order,
                    offer_id,
                    template_id,
                    introduced_day,
                    deadline_day
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        slot_name,
                        index,
                        event.active_offer_id(),
                        event.base_template_id(),
                        event.introduced_day,
                        event.deadline_day,
                    )
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


def _load_active_events(
    connection,
    slot_name: str,
    event_map: dict[str, Event],
) -> list[Event]:
    offer_rows = connection.execute(
        """
        SELECT offer_id, template_id, introduced_day, deadline_day
        FROM save_event_offers
        WHERE slot_name = ?
        ORDER BY sort_order
        """,
        (slot_name,),
    ).fetchall()
    if offer_rows:
        active_events: list[Event] = []
        for row in offer_rows:
            template = event_map.get(row["template_id"])
            if template is None:
                raise ValueError(
                    f"Saved event template '{row['template_id']}' is not defined."
                )
            active_events.append(
                Event(
                    id=template.id,
                    title=template.title,
                    description=template.description,
                    check_stats=template.check_stats,
                    difficulty=template.difficulty,
                    required_tags=template.required_tags,
                    required_card_ids=template.required_card_ids,
                    bonus_tags=template.bonus_tags,
                    reward_card_ids=template.reward_card_ids,
                    success_delta=template.success_delta,
                    failure_delta=template.failure_delta,
                    success_text=template.success_text,
                    failure_text=template.failure_text,
                    kind=template.kind,
                    source=template.source,
                    time_cost=template.time_cost,
                    payout=template.payout,
                    deadline_days=template.deadline_days,
                    template_id=template.base_template_id(),
                    offer_id=row["offer_id"],
                    introduced_day=row["introduced_day"],
                    deadline_day=row["deadline_day"],
                    storyline_id=template.storyline_id,
                    chain_step=template.chain_step,
                )
            )
        return active_events

    event_rows = connection.execute(
        """
        SELECT event_id
        FROM save_events
        WHERE slot_name = ?
        ORDER BY sort_order
        """,
        (slot_name,),
    ).fetchall()
    active_events = []
    for row in event_rows:
        template = event_map.get(row["event_id"])
        if template is None:
            raise ValueError(f"Saved event '{row['event_id']}' is not defined in the catalog.")
        active_events.append(template)
    return active_events


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

        run_state_row = connection.execute(
            """
            SELECT
                day,
                actions_remaining,
                money,
                special_chain_progress,
                special_chain_failed,
                offer_sequence,
                tavern_visits_today
            FROM save_run_state
            WHERE slot_name = ?
            """,
            (slot_name,),
        ).fetchone()

        card_rows = connection.execute(
            """
            SELECT
                instance_id,
                card_id,
                power_bonus,
                current_durability,
                nickname,
                equipped_to_instance_id,
                busy_until_day
            FROM save_card_instances
            WHERE slot_name = ?
            ORDER BY instance_id
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
    event_templates = build_story_events(db_path)
    event_map = {event.base_template_id(): event for event in event_templates}

    with connect_database(db_path) as connection:
        remaining_events = _load_active_events(connection, slot_name, event_map)

    collection = {
        row["instance_id"]: CardInstance(
            instance_id=row["instance_id"],
            card_id=row["card_id"],
            power_bonus=row["power_bonus"],
            current_durability=row["current_durability"],
            nickname=row["nickname"],
            equipped_to_instance_id=row["equipped_to_instance_id"],
            busy_until_day=row["busy_until_day"],
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
        event_library=event_map,
        day=run_state_row["day"] if run_state_row is not None else 1,
        money=run_state_row["money"] if run_state_row is not None else 0,
        special_chain_progress=run_state_row["special_chain_progress"] if run_state_row is not None else 0,
        special_chain_failed=bool(run_state_row["special_chain_failed"]) if run_state_row is not None else False,
        offer_sequence=run_state_row["offer_sequence"] if run_state_row is not None else 0,
        tavern_visits_today=run_state_row["tavern_visits_today"] if run_state_row is not None else 0,
        auto_plan_day_on_init=False,
    )
