from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CardCategory(StrEnum):
    PERSON = "person"
    INFO = "info"
    EQUIPMENT = "equipment"


@dataclass(frozen=True)
class CardDefinition:
    id: str
    name: str
    category: CardCategory
    tags: tuple[str, ...]
    description: str
    power: int = 1
    max_durability: int = 3
    rarity: str = "common"


@dataclass
class CardInstance:
    instance_id: str
    card_id: str
    power_bonus: int = 0
    current_durability: int = 0
    nickname: str = ""
    equipped_to_instance_id: str = ""

    def effective_power(self, card: CardDefinition, extra_bonus: int = 0) -> int:
        return max(card.power + self.power_bonus + extra_bonus, 0)

    def display_name(self, card: CardDefinition) -> str:
        return self.nickname or card.name

    def is_usable(self) -> bool:
        return self.current_durability > 0

    def is_equipped(self) -> bool:
        return bool(self.equipped_to_instance_id)


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    description: str
    required_tags: tuple[str, ...]
    required_card_ids: tuple[str, ...] = ()
    bonus_tags: tuple[str, ...] = ()
    reward_card_ids: tuple[str, ...] = ()
    success_delta: int = 1
    failure_delta: int = -1
    success_text: str = ""
    failure_text: str = ""


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
