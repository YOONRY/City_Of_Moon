from __future__ import annotations

from pathlib import Path
import sqlite3

from .database import connect_database, initialize_database
from .models import CardCategory, CardDefinition, CardInstance, Event, EventKind

EVENT_TEMPLATE_OVERRIDES: dict[str, dict[str, object]] = {
    "market_riot": {
        "kind": EventKind.SPECIAL,
        "source": "story",
        "time_cost": 2,
        "payout": 8,
        "deadline_days": 5,
        "storyline_id": "moonlit_city",
        "chain_step": 1,
    },
    "masked_ball": {
        "kind": EventKind.SPECIAL,
        "source": "story",
        "time_cost": 2,
        "payout": 12,
        "deadline_days": 6,
        "storyline_id": "moonlit_city",
        "chain_step": 2,
    },
    "eclipse_shrine": {
        "kind": EventKind.SPECIAL,
        "source": "story",
        "time_cost": 2,
        "payout": 15,
        "deadline_days": 7,
        "storyline_id": "moonlit_city",
        "chain_step": 3,
    },
    "broken_rail": {
        "kind": EventKind.INCIDENT,
        "source": "street",
        "time_cost": 1,
        "payout": 6,
        "deadline_days": 1,
    },
    "smuggler_tunnel": {
        "kind": EventKind.INCIDENT,
        "source": "street",
        "time_cost": 1,
        "payout": 7,
        "deadline_days": 1,
    },
    "icewind_crossing": {
        "kind": EventKind.INCIDENT,
        "source": "street",
        "time_cost": 2,
        "payout": 10,
        "deadline_days": 1,
    },
}


def build_contract_templates() -> list[Event]:
    return [
        Event(
            id="daily_message_run",
            title="등불가의 전갈 운반",
            description="밤거리 연락망이 끊기지 않도록 은밀하게 전갈을 이어 달라는 의뢰다.",
            check_stats=("agility", "charm"),
            difficulty=3,
            required_tags=("street", "covert"),
            bonus_tags=("route",),
            person_slots=1,
            info_slots=1,
            success_delta=0,
            failure_delta=0,
            success_text="연락망이 끊기지 않도록 전갈을 끝까지 이어 붙였다.",
            failure_text="연락꾼이 늦어 도시 하층의 신뢰를 조금 잃었다.",
            kind=EventKind.DAILY,
            source="board",
            time_cost=1,
            payout=5,
            deadline_days=1,
            template_id="daily_message_run",
        ),
        Event(
            id="daily_guild_ledger",
            title="길드 장부 정리",
            description="상단과 공방 조합의 장부를 맞춰 달라는 짧지만 까다로운 실무 의뢰다.",
            check_stats=("intelligence", "charm"),
            difficulty=4,
            required_tags=("negotiation", "public"),
            bonus_tags=("permit",),
            person_slots=1,
            info_slots=1,
            success_delta=0,
            failure_delta=0,
            success_text="장부 차이를 정리해 상단의 의심을 잠재웠다.",
            failure_text="장부 정리가 틀어져 의뢰인은 만족하지 못했다.",
            kind=EventKind.DAILY,
            source="board",
            time_cost=1,
            payout=6,
            deadline_days=1,
            template_id="daily_guild_ledger",
        ),
        Event(
            id="daily_bodyguard_shift",
            title="상단 호위 교대",
            description="물품 교대 시간이 겹친 상단 호위 임무다. 하루를 거의 통째로 비워야 한다.",
            check_stats=("strength", "charm"),
            difficulty=5,
            required_tags=("escort", "public"),
            bonus_tags=("support",),
            person_slots=2,
            info_slots=0,
            success_delta=0,
            failure_delta=0,
            success_text="호위 교대를 무사히 끝내고 상단 측 신뢰를 얻었다.",
            failure_text="호위선이 흔들려 의뢰 대금을 제대로 받지 못했다.",
            kind=EventKind.DAILY,
            source="board",
            time_cost=2,
            payout=9,
            deadline_days=1,
            template_id="daily_bodyguard_shift",
        ),
        Event(
            id="daily_clinic_supply",
            title="진료소 보급 회수",
            description="변두리 진료소에서 필요한 의약품 상자를 회수해 옮기는 의뢰다.",
            check_stats=("strength", "intelligence"),
            difficulty=4,
            required_tags=("support", "medical"),
            bonus_tags=("street",),
            person_slots=1,
            info_slots=0,
            success_delta=0,
            failure_delta=0,
            success_text="보급 상자를 무사히 회수해 진료소를 살렸다.",
            failure_text="보급 상자가 중간에 새며 일정이 꼬였다.",
            kind=EventKind.DAILY,
            source="board",
            time_cost=1,
            payout=7,
            deadline_days=1,
            template_id="daily_clinic_supply",
        ),
        Event(
            id="tavern_rumor_cache",
            title="술집 소문: 밀수 창고",
            description="술집에서 흘러나온 밀수 창고 소문을 따라가면 숨겨진 물건을 건질 수 있다.",
            check_stats=("intelligence", "agility"),
            difficulty=5,
            required_tags=("street", "evidence"),
            bonus_tags=("covert",),
            reward_card_ids=("oracle_lens",),
            person_slots=1,
            info_slots=1,
            success_delta=0,
            failure_delta=0,
            success_text="창고의 비밀 통로를 찾아 유용한 기록 렌즈를 손에 넣었다.",
            failure_text="소문은 사실이었지만 이미 누군가 먼저 치운 뒤였다.",
            kind=EventKind.INCIDENT,
            source="tavern",
            time_cost=1,
            payout=4,
            deadline_days=1,
            template_id="tavern_rumor_cache",
        ),
        Event(
            id="tavern_backroom_duel",
            title="술집 소동: 뒷방 결투",
            description="술집 뒷방에서 벌어진 결투 소동에 끼어들면 인맥이나 장비를 챙길 수 있다.",
            check_stats=("strength", "charm"),
            difficulty=5,
            required_tags=("combat", "escort"),
            bonus_tags=("public",),
            reward_card_ids=("heirloom_blade",),
            person_slots=2,
            info_slots=0,
            success_delta=0,
            failure_delta=0,
            success_text="결투를 정리하고 오래된 칼 한 자루를 사례로 받았다.",
            failure_text="소동을 잠재우지 못하고 뒷골목의 평판만 조금 깎였다.",
            kind=EventKind.INCIDENT,
            source="tavern",
            time_cost=1,
            payout=3,
            deadline_days=1,
            template_id="tavern_backroom_duel",
        ),
    ]


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
                equipped_to_instance_id,
                busy_until_day
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
            busy_until_day=row["busy_until_day"],
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
                equipment_slot,
                info_kind,
                description,
                strength,
                agility,
                intelligence,
                charm,
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
            equipment_slot=row["equipment_slot"],
            info_kind=row["info_kind"],
            tags=tag_map.get(row["id"], ()),
            description=row["description"],
            strength=row["strength"],
            agility=row["agility"],
            intelligence=row["intelligence"],
            charm=row["charm"],
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
        check_stat_map = _load_grouped_values(
            connection,
            "event_check_stats",
            "event_id",
            "stat_name",
        )
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                description,
                difficulty,
                person_slots,
                info_slots,
                success_delta,
                failure_delta,
                success_text,
                failure_text
            FROM events
            ORDER BY sort_order
            """
        ).fetchall()
    database_events = [
        Event(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            check_stats=check_stat_map.get(row["id"], ()),
            difficulty=row["difficulty"],
            required_tags=required_tag_map.get(row["id"], ()),
            required_card_ids=required_card_map.get(row["id"], ()),
            bonus_tags=bonus_tag_map.get(row["id"], ()),
            reward_card_ids=reward_map.get(row["id"], ()),
            person_slots=row["person_slots"],
            info_slots=row["info_slots"],
            success_delta=row["success_delta"],
            failure_delta=row["failure_delta"],
            success_text=row["success_text"],
            failure_text=row["failure_text"],
            kind=EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("kind", EventKind.DAILY),
            source=str(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("source", "board")),
            time_cost=int(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("time_cost", 1)),
            payout=int(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("payout", 0)),
            deadline_days=int(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("deadline_days", 1)),
            template_id=row["id"],
            storyline_id=str(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("storyline_id", "")),
            chain_step=int(EVENT_TEMPLATE_OVERRIDES.get(row["id"], {}).get("chain_step", 0)),
        )
        for row in rows
    ]
    return database_events + build_contract_templates()
