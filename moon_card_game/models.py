from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

STAT_FIELDS = ("strength", "agility", "intelligence", "charm")


class CardCategory(StrEnum):
    PERSON = "person"
    INFO = "info"
    EQUIPMENT = "equipment"


class EquipmentSlot(StrEnum):
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"


class EventKind(StrEnum):
    DAILY = "daily"
    INCIDENT = "incident"
    SPECIAL = "special"


@dataclass(frozen=True)
class CardDefinition:
    id: str
    name: str
    category: CardCategory
    tags: tuple[str, ...]
    description: str
    info_kind: str = ""
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    charm: int = 0
    max_durability: int = 3
    rarity: str = "common"
    equipment_slot: str = ""

    def stats(self) -> dict[str, int]:
        return {
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "charm": self.charm,
        }

    def is_general_info(self) -> bool:
        return self.category == CardCategory.INFO and self.info_kind == "general"

    def is_exclusive_info(self) -> bool:
        return self.category == CardCategory.INFO and self.info_kind == "exclusive"

    def is_equipment(self) -> bool:
        return self.category == CardCategory.EQUIPMENT


@dataclass
class CardInstance:
    instance_id: str
    card_id: str
    power_bonus: int = 0
    current_durability: int = 0
    nickname: str = ""
    equipped_to_instance_id: str = ""
    busy_until_day: int = 0

    def stat_value(self, card: CardDefinition, stat_name: str, extra_bonus: int = 0) -> int:
        return max(getattr(card, stat_name) + extra_bonus, 0)

    def effective_stats(
        self,
        card: CardDefinition,
        extra_bonuses: dict[str, int] | None = None,
    ) -> dict[str, int]:
        bonuses = extra_bonuses or {}
        return {
            stat_name: self.stat_value(card, stat_name, bonuses.get(stat_name, 0))
            for stat_name in STAT_FIELDS
        }

    def check_bonus(self) -> int:
        return max(self.power_bonus, 0)

    def display_name(self, card: CardDefinition) -> str:
        return self.nickname or card.name

    def is_usable(self) -> bool:
        return True

    def is_available(self, current_day: int) -> bool:
        return self.busy_until_day < current_day

    def is_equipped(self) -> bool:
        return bool(self.equipped_to_instance_id)


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    description: str
    check_stats: tuple[str, ...]
    difficulty: int
    required_tags: tuple[str, ...]
    required_card_ids: tuple[str, ...] = ()
    bonus_tags: tuple[str, ...] = ()
    reward_card_ids: tuple[str, ...] = ()
    person_slots: int = 1
    info_slots: int = 0
    success_delta: int = 1
    failure_delta: int = -1
    success_text: str = ""
    failure_text: str = ""
    kind: EventKind = EventKind.DAILY
    source: str = "board"
    time_cost: int = 1
    payout: int = 0
    deadline_days: int = 1
    template_id: str = ""
    offer_id: str = ""
    introduced_day: int = 1
    deadline_day: int = 0
    storyline_id: str = ""
    chain_step: int = 0

    def base_template_id(self) -> str:
        return self.template_id or self.id

    def active_offer_id(self) -> str:
        return self.offer_id or self.id

    def is_daily(self) -> bool:
        return self.kind == EventKind.DAILY

    def is_incident(self) -> bool:
        return self.kind == EventKind.INCIDENT

    def is_special(self) -> bool:
        return self.kind == EventKind.SPECIAL


@dataclass(frozen=True)
class Resolution:
    event: Event
    card: CardDefinition | None
    card_instance: CardInstance | None
    success: bool
    score: int
    stability_delta: int
    reward_card: CardDefinition | None
    reward_instance: CardInstance | None
    message: str
    money_delta: int = 0
    time_cost: int = 0
    days_advanced: int = 0
