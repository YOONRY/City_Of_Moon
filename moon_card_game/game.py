from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from random import Random

from .content import build_card_catalog, build_story_events, build_starter_collection
from .models import CardCategory, CardDefinition, CardInstance, Event, Resolution

HAND_SIZE = 4
STARTING_STABILITY = 3


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
            if card_instance.is_usable()
        ]

    def refill_draw_pile_from_discard(self) -> None:
        usable_cards = [
            instance_id
            for instance_id in self.discard_pile
            if self.collection[instance_id].is_usable()
        ]
        worn_out_cards = [
            instance_id
            for instance_id in self.discard_pile
            if not self.collection[instance_id].is_usable()
        ]
        self.draw_pile = usable_cards
        self.discard_pile = worn_out_cards
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

    def add_card_to_collection(
        self,
        card_id: str,
        power_bonus: int = 0,
        current_durability: int | None = None,
        nickname: str = "",
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
        )
        self.collection[instance.instance_id] = instance
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
                self.catalog[card_instance.card_id].name,
                card_instance.instance_id,
            ),
        )
        for card_instance in ordered_cards:
            category = self.catalog[card_instance.card_id].category
            grouped.setdefault(category, []).append(card_instance)
        return {
            category: grouped[category]
            for category in sorted(grouped, key=lambda item: item.value)
        }

    def play_card(self, hand_index: int) -> Resolution:
        event = self.current_event()
        if event is None:
            raise ValueError("No event is available.")
        if hand_index < 0 or hand_index >= len(self.hand):
            raise IndexError("Card selection is out of range.")

        instance_id = self.hand.pop(hand_index)
        card_instance = self.collection[instance_id]
        card = self.catalog[card_instance.card_id]

        self.discard_pile.append(instance_id)
        card_instance.current_durability = max(card_instance.current_durability - 1, 0)
        self.events.pop(0)

        resolution = resolve_event(event, card, card_instance, self.catalog)
        self.stability += resolution.stability_delta
        self.completed_events += 1

        if resolution.reward_card is not None:
            reward_instance = self.add_card_to_collection(resolution.reward_card.id)
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
            message=event.failure_text or "You let the moment pass and the city paid the price.",
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
) -> Resolution:
    required_hits = sum(1 for tag in card.tags if tag in event.required_tags)
    bonus_hits = sum(1 for tag in card.tags if tag in event.bonus_tags)
    score = required_hits * 2 + bonus_hits + max(card_instance.effective_power(card) - 1, 0)
    success = required_hits > 0
    stability_delta = event.success_delta + min(bonus_hits, 1) if success else event.failure_delta
    reward_card = catalog[event.reward_card_ids[0]] if success and event.reward_card_ids else None
    if success:
        message = event.success_text or "The card fits the moment and the city bends in your favor."
    else:
        message = event.failure_text or "The card fails to answer the crisis."
    return Resolution(
        event=event,
        card=card,
        card_instance=card_instance,
        success=success,
        score=score,
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
