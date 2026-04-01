from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from random import Random

from .content import build_card_catalog, build_story_events, build_starter_collection
from .models import (
    STAT_FIELDS,
    CardCategory,
    CardDefinition,
    CardInstance,
    Event,
    Resolution,
)

HAND_SIZE = 4
STARTING_STABILITY = 3
CARD_CATEGORY_ORDER = {
    CardCategory.PERSON: 0,
    CardCategory.INFO: 1,
    CardCategory.EQUIPMENT: 2,
}


@dataclass
class GameState:
    catalog: dict[str, CardDefinition]
    events: list[Event]
    collection: dict[str, CardInstance]
    rng: Random = field(default_factory=Random)
    stability: int = STARTING_STABILITY
    draw_pile: list[str] = field(default_factory=list)
    discard_pile: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    completed_events: int = 0
    auto_draw_on_init: bool = True

    def __post_init__(self) -> None:
        self.normalize_equipment_assignments()
        self.sanitize_piles()
        if not self.auto_draw_on_init:
            return
        if not self.draw_pile:
            self.draw_pile = self.build_draw_pile_from_collection()
            self.rng.shuffle(self.draw_pile)
        self.draw_to_hand()

    def build_draw_pile_from_collection(self) -> list[str]:
        return [
            instance_id
            for instance_id, card_instance in self.collection.items()
            if self.is_drawable_card(instance_id) and card_instance.is_usable()
        ]

    def sanitize_piles(self) -> None:
        active_ids = {
            instance_id
            for instance_id, card_instance in self.collection.items()
            if self.is_drawable_card(instance_id) and card_instance.is_usable()
        }
        self.hand = [instance_id for instance_id in self.hand if instance_id in active_ids]
        self.draw_pile = [
            instance_id for instance_id in self.draw_pile if instance_id in active_ids
        ]
        self.discard_pile = [
            instance_id for instance_id in self.discard_pile if instance_id in active_ids
        ]

    def refill_draw_pile_from_discard(self) -> None:
        usable_cards = [
            instance_id
            for instance_id in self.discard_pile
            if instance_id in self.collection
            and self.is_drawable_card(instance_id)
            and self.collection[instance_id].is_usable()
        ]
        self.draw_pile = usable_cards
        self.discard_pile = [
            instance_id
            for instance_id in self.discard_pile
            if instance_id not in usable_cards
        ]
        self.rng.shuffle(self.draw_pile)

    def draw_to_hand(self, target_size: int = HAND_SIZE) -> None:
        while len(self.hand) < target_size:
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                self.refill_draw_pile_from_discard()
                if not self.draw_pile:
                    break
            self.hand.append(self.draw_pile.pop())

    def current_event(self) -> Event | None:
        if not self.events:
            return None
        return self.events[0]

    def card_instance(self, instance_id: str) -> CardInstance:
        return self.collection[instance_id]

    def card_definition(self, instance_id: str) -> CardDefinition:
        return self.catalog[self.collection[instance_id].card_id]

    def next_instance_id(self, card_id: str) -> str:
        index = 1
        while True:
            candidate = f"{card_id}_instance_{index}"
            if candidate not in self.collection:
                return candidate
            index += 1

    def is_drawable_card(self, instance_id: str) -> bool:
        card = self.card_definition(instance_id)
        return card.category == CardCategory.PERSON or card.is_general_info()

    def owns_required_info(self, event: Event) -> bool:
        owned_card_ids = {card_instance.card_id for card_instance in self.collection.values()}
        return all(card_id in owned_card_ids for card_id in event.required_card_ids)

    def person_instance_ids(self) -> list[str]:
        people = [
            card_instance.instance_id
            for card_instance in self.collection.values()
            if self.catalog[card_instance.card_id].category == CardCategory.PERSON
        ]
        return sorted(
            people,
            key=lambda instance_id: (
                self.catalog[self.collection[instance_id].card_id].name,
                instance_id,
            ),
        )

    def equipment_for(self, person_instance_id: str) -> list[CardInstance]:
        equipment = [
            card_instance
            for card_instance in self.collection.values()
            if self.catalog[card_instance.card_id].category == CardCategory.EQUIPMENT
            and card_instance.equipped_to_instance_id == person_instance_id
        ]
        return sorted(
            equipment,
            key=lambda item: (self.catalog[item.card_id].name, item.instance_id),
        )

    def equipment_bonus_for(self, person_instance_id: str) -> dict[str, int]:
        totals = {stat_name: 0 for stat_name in STAT_FIELDS}
        for equipment_instance in self.equipment_for(person_instance_id):
            if not equipment_instance.is_usable():
                continue
            equipment_card = self.catalog[equipment_instance.card_id]
            equipment_stats = equipment_instance.effective_stats(equipment_card)
            for stat_name in STAT_FIELDS:
                totals[stat_name] += equipment_stats[stat_name]
        return totals

    def effective_stats(self, instance_id: str) -> dict[str, int]:
        card_instance = self.card_instance(instance_id)
        card = self.card_definition(instance_id)
        extra_bonuses = (
            self.equipment_bonus_for(instance_id)
            if card.category == CardCategory.PERSON
            else {stat_name: 0 for stat_name in STAT_FIELDS}
        )
        return card_instance.effective_stats(card, extra_bonuses)

    def event_check_total(
        self,
        instance_id: str,
        event: Event,
        support_instance_id: str | None = None,
    ) -> int:
        stats = self.effective_stats(instance_id)
        total = sum(stats.get(stat_name, 0) for stat_name in event.check_stats)
        total += self.card_instance(instance_id).check_bonus()
        if support_instance_id is not None:
            support_stats = self.effective_stats(support_instance_id)
            total += sum(support_stats.get(stat_name, 0) for stat_name in event.check_stats)
            total += self.card_instance(support_instance_id).check_bonus()
        return total

    def default_equipment_target(self) -> str | None:
        people = self.person_instance_ids()
        if not people:
            return None
        people_by_load = sorted(
            people,
            key=lambda instance_id: (
                len(self.equipment_for(instance_id)),
                self.catalog[self.collection[instance_id].card_id].name,
                instance_id,
            ),
        )
        return people_by_load[0]

    def attach_equipment(
        self,
        equipment_instance_id: str,
        target_instance_id: str | None = None,
    ) -> None:
        equipment_instance = self.collection[equipment_instance_id]
        equipment_card = self.catalog[equipment_instance.card_id]
        if equipment_card.category != CardCategory.EQUIPMENT:
            raise ValueError("Only equipment cards can be attached.")

        resolved_target = target_instance_id or self.default_equipment_target()
        if resolved_target is None:
            equipment_instance.equipped_to_instance_id = ""
            return
        if self.catalog[self.collection[resolved_target].card_id].category != CardCategory.PERSON:
            raise ValueError("Equipment can only be attached to a person card.")
        equipment_instance.equipped_to_instance_id = resolved_target

    def normalize_equipment_assignments(self) -> None:
        valid_people = set(self.person_instance_ids())
        for equipment_instance in sorted(
            (
                card_instance
                for card_instance in self.collection.values()
                if self.catalog[card_instance.card_id].category == CardCategory.EQUIPMENT
            ),
            key=lambda item: (self.catalog[item.card_id].name, item.instance_id),
        ):
            if equipment_instance.equipped_to_instance_id in valid_people:
                continue
            self.attach_equipment(equipment_instance.instance_id)

    def add_card_to_collection(
        self,
        card_id: str,
        power_bonus: int = 0,
        current_durability: int | None = None,
        nickname: str = "",
        equipped_to_instance_id: str = "",
    ) -> CardInstance:
        card = self.catalog[card_id]
        instance = CardInstance(
            instance_id=self.next_instance_id(card_id),
            card_id=card_id,
            power_bonus=power_bonus,
            current_durability=(
                current_durability
                if current_durability is not None
                else card.max_durability
            ),
            nickname=nickname,
            equipped_to_instance_id=(
                equipped_to_instance_id if card.category == CardCategory.EQUIPMENT else ""
            ),
        )
        self.collection[instance.instance_id] = instance
        if card.category == CardCategory.EQUIPMENT:
            self.attach_equipment(instance.instance_id, equipped_to_instance_id or None)
        return instance

    def total_cards_owned(self) -> int:
        return len(self.collection)

    def unique_cards_owned(self) -> int:
        return len({card_instance.card_id for card_instance in self.collection.values()})

    def collection_by_category(self) -> dict[CardCategory, list[CardInstance]]:
        grouped: dict[CardCategory, list[CardInstance]] = {}
        ordered_cards = sorted(
            self.collection.values(),
            key=lambda card_instance: (
                CARD_CATEGORY_ORDER[self.catalog[card_instance.card_id].category],
                self.catalog[card_instance.card_id].name,
                card_instance.instance_id,
            ),
        )
        for card_instance in ordered_cards:
            category = self.catalog[card_instance.card_id].category
            grouped.setdefault(category, []).append(card_instance)
        return {
            category: grouped[category]
            for category in sorted(grouped, key=lambda item: CARD_CATEGORY_ORDER[item])
        }

    def play_card(
        self,
        hand_index: int,
        support_hand_index: int | None = None,
    ) -> Resolution:
        event = self.current_event()
        if event is None:
            raise ValueError("No event is available.")
        if hand_index < 0 or hand_index >= len(self.hand):
            raise IndexError("Card selection is out of range.")
        if support_hand_index is not None:
            if support_hand_index < 0 or support_hand_index >= len(self.hand):
                raise IndexError("Support card selection is out of range.")
            if support_hand_index == hand_index:
                raise ValueError("Support card must be different from the primary card.")

        primary_instance_id = self.hand[hand_index]
        primary_instance = self.collection[primary_instance_id]
        primary_card = self.catalog[primary_instance.card_id]
        if primary_card.category != CardCategory.PERSON:
            raise ValueError("The primary card must be a person card.")

        support_instance_id = None
        support_instance = None
        support_card = None
        if support_hand_index is not None:
            support_instance_id = self.hand[support_hand_index]
            support_instance = self.collection[support_instance_id]
            support_card = self.catalog[support_instance.card_id]
            if not support_card.is_general_info():
                raise ValueError("The support card must be a general info card.")

        removal_indexes = sorted(
            index
            for index in [hand_index, support_hand_index]
            if index is not None
        )
        removed_instance_ids = [self.hand[index] for index in removal_indexes]
        for index in reversed(removal_indexes):
            self.hand.pop(index)

        for instance_id in removed_instance_ids:
            played_instance = self.collection[instance_id]
            self.discard_pile.append(instance_id)
            played_instance.current_durability = max(played_instance.current_durability - 1, 0)

        self.events.pop(0)

        resolution = resolve_event(
            event,
            primary_card,
            primary_instance,
            self.catalog,
            effective_stats=self.effective_stats(primary_instance_id),
            support_card=support_card,
            support_instance=support_instance,
            support_stats=(
                self.effective_stats(support_instance_id)
                if support_instance_id is not None
                else None
            ),
            has_required_info=self.owns_required_info(event),
        )
        self.stability += resolution.stability_delta
        self.completed_events += 1

        if resolution.reward_card is not None:
            reward_instance = self.add_card_to_collection(resolution.reward_card.id)
            reward_card = self.catalog[reward_instance.card_id]
            if reward_card.category == CardCategory.PERSON or reward_card.is_general_info():
                self.discard_pile.append(reward_instance.instance_id)
            resolution = replace(resolution, reward_instance=reward_instance)

        self.draw_to_hand()
        return resolution

    def skip_event(self) -> Resolution:
        event = self.current_event()
        if event is None:
            raise ValueError("No event is available.")

        self.events.pop(0)
        self.stability += event.failure_delta
        self.completed_events += 1
        self.draw_to_hand()
        return Resolution(
            event=event,
            card=None,
            card_instance=None,
            success=False,
            score=0,
            stability_delta=event.failure_delta,
            reward_card=None,
            reward_instance=None,
            message=event.failure_text or "의뢰를 흘려보냈고 도시의 분위기가 더 무거워졌습니다.",
        )

    def is_won(self) -> bool:
        return not self.events and self.stability > 0

    def is_lost(self) -> bool:
        return self.stability <= 0


def resolve_event(
    event: Event,
    card: CardDefinition,
    card_instance: CardInstance,
    catalog: dict[str, CardDefinition],
    effective_stats: dict[str, int] | None = None,
    support_card: CardDefinition | None = None,
    support_instance: CardInstance | None = None,
    support_stats: dict[str, int] | None = None,
    has_required_info: bool = True,
) -> Resolution:
    stats = dict(effective_stats or card_instance.effective_stats(card))
    if support_card is not None and support_instance is not None and support_stats is not None:
        for stat_name in STAT_FIELDS:
            stats[stat_name] += support_stats.get(stat_name, 0)
    check_total = sum(stats.get(stat_name, 0) for stat_name in event.check_stats)
    check_total += card_instance.check_bonus()
    if support_instance is not None:
        check_total += support_instance.check_bonus()
    success = has_required_info and check_total >= event.difficulty
    stability_delta = event.success_delta if success else event.failure_delta
    reward_card = catalog[event.reward_card_ids[0]] if success and event.reward_card_ids else None

    if success:
        if support_card is not None:
            message = (
                event.success_text
                or f"{support_instance.display_name(support_card)}의 정보 지원으로 체크를 돌파했습니다."
            )
        else:
            message = event.success_text or "스탯 체크를 통과하며 사건을 원하는 쪽으로 밀어냈습니다."
    elif event.required_card_ids and not has_required_info:
        required_names = ", ".join(
            catalog[card_id].name
            for card_id in event.required_card_ids
            if card_id in catalog
        )
        message = (
            f"전용 정보 [{required_names}]가 없어 사건의 핵심에 접근하지 못했습니다."
            if required_names
            else "필요한 전용 정보가 없어 사건의 핵심에 접근하지 못했습니다."
        )
    else:
        message = (
            event.failure_text
            or f"체크 수치 {check_total}가 목표치 {event.difficulty}에 미치지 못했습니다."
        )

    return Resolution(
        event=event,
        card=card,
        card_instance=card_instance,
        success=success,
        score=check_total,
        stability_delta=stability_delta,
        reward_card=reward_card,
        reward_instance=None,
        message=message,
    )


def create_default_game(
    seed: int | None = None,
    db_path: str | Path | None = None,
) -> GameState:
    rng = Random(seed)
    return GameState(
        catalog=build_card_catalog(db_path),
        events=build_story_events(db_path),
        collection=build_starter_collection(db_path),
        rng=rng,
    )
