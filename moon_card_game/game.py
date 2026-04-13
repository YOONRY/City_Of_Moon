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
    EventKind,
    Resolution,
)

STARTING_STABILITY = 3
STARTING_MONEY = 8
WEEKLY_TAX_AMOUNT = 12
WEEKLY_TAX_STABILITY_PENALTY = 2
INCIDENT_CHANCE = 0.35
TAVERN_VISIT_COST = 2
CARD_CATEGORY_ORDER = {
    CardCategory.PERSON: 0,
    CardCategory.INFO: 1,
    CardCategory.EQUIPMENT: 2,
}
EVENT_KIND_ORDER = {
    EventKind.INCIDENT: 0,
    EventKind.DAILY: 1,
    EventKind.SPECIAL: 2,
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
    event_library: dict[str, Event] = field(default_factory=dict)
    day: int = 1
    money: int = STARTING_MONEY
    weekly_tax_amount: int = WEEKLY_TAX_AMOUNT
    special_chain_progress: int = 0
    special_chain_failed: bool = False
    offer_sequence: int = 0
    tavern_visits_today: int = 0
    auto_plan_day_on_init: bool = True

    def __post_init__(self) -> None:
        self.normalize_equipment_assignments()
        self._initialize_event_library()
        self.events = [self._ensure_offer(event) for event in self.events]
        self.sort_events()
        if not self.events and self.event_library and self.auto_plan_day_on_init:
            self.refresh_day_board()
        self.sanitize_piles()

    def _initialize_event_library(self) -> None:
        if self.event_library:
            self.event_library = {
                event.base_template_id(): replace(
                    event,
                    template_id=event.base_template_id(),
                    offer_id="",
                    deadline_day=0,
                )
                for event in self.event_library.values()
            }
            return
        self.event_library = {
            event.base_template_id(): replace(
                event,
                template_id=event.base_template_id(),
                offer_id="",
                deadline_day=0,
            )
            for event in self.events
        }

    def _ensure_offer(self, event: Event) -> Event:
        template_id = event.base_template_id()
        if template_id not in self.event_library:
            self.event_library[template_id] = replace(
                event,
                template_id=template_id,
                offer_id="",
                deadline_day=0,
            )
        if event.offer_id:
            return event
        return replace(
            event,
            template_id=template_id,
            offer_id=self._next_offer_id(template_id),
            introduced_day=event.introduced_day or self.day,
            deadline_day=(
                event.deadline_day
                if event.deadline_day > 0
                else (event.introduced_day or self.day) + max(event.deadline_days, 1) - 1
            ),
        )

    def _next_offer_id(self, template_id: str) -> str:
        self.offer_sequence += 1
        return f"{template_id}__d{self.day}_n{self.offer_sequence}"

    def hand_sort_key(self, instance_id: str) -> tuple[int, str, str]:
        card = self.card_definition(instance_id)
        return (
            CARD_CATEGORY_ORDER[card.category],
            card.name,
            instance_id,
        )

    def build_draw_pile_from_collection(self) -> list[str]:
        return [
            instance_id
            for instance_id in sorted(self.collection, key=self.hand_sort_key)
            if self.is_drawable_card(instance_id)
        ]

    def sanitize_piles(self) -> None:
        self.hand = self.build_draw_pile_from_collection()
        self.draw_pile = []
        self.discard_pile = []

    def refill_draw_pile_from_discard(self) -> None:
        self.sanitize_piles()

    def draw_to_hand(self) -> None:
        self.sanitize_piles()

    def current_event(self) -> Event | None:
        if not self.events:
            return None
        return self.events[0]

    def next_tax_day(self) -> int:
        current_week = (self.day - 1) // 7
        return (current_week + 1) * 7 + 1

    def days_until_tax(self) -> int:
        return self.next_tax_day() - self.day

    def card_instance(self, instance_id: str) -> CardInstance:
        return self.collection[instance_id]

    def card_definition(self, instance_id: str) -> CardDefinition:
        return self.catalog[self.collection[instance_id].card_id]

    def template_event(self, template_id: str) -> Event:
        return self.event_library[template_id]

    def next_instance_id(self, card_id: str) -> str:
        index = 1
        while True:
            candidate = f"{card_id}_instance_{index}"
            if candidate not in self.collection:
                return candidate
            index += 1

    def is_drawable_card(self, instance_id: str) -> bool:
        card = self.card_definition(instance_id)
        return card.category == CardCategory.PERSON or card.category == CardCategory.INFO

    def is_card_available(self, instance_id: str) -> bool:
        return self.collection[instance_id].is_available(self.day)

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

    def usable_person_instance_ids(self) -> list[str]:
        return [
            instance_id
            for instance_id in self.person_instance_ids()
            if self.is_card_available(instance_id)
        ]

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

    def equipped_item_for_slot(
        self,
        person_instance_id: str,
        equipment_slot: str,
    ) -> CardInstance | None:
        for equipment_instance in self.equipment_for(person_instance_id):
            equipment_card = self.catalog[equipment_instance.card_id]
            if equipment_card.equipment_slot == equipment_slot:
                return equipment_instance
        return None

    def equipment_bonus_for(self, person_instance_id: str) -> dict[str, int]:
        totals = {stat_name: 0 for stat_name in STAT_FIELDS}
        for equipment_instance in self.equipment_for(person_instance_id):
            if not equipment_instance.is_available(self.day):
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

    def can_assign_person_to_event(self, person_instance_id: str, event: Event) -> bool:
        if person_instance_id not in self.collection:
            return False
        person_card = self.card_definition(person_instance_id)
        person_instance = self.card_instance(person_instance_id)
        return (
            person_card.category == CardCategory.PERSON
            and person_instance.is_available(self.day)
            and self.owns_required_info(event)
        )

    def actionable_events(self) -> list[Event]:
        usable_people = self.usable_person_instance_ids()
        actionable: list[Event] = []
        for event in self.events:
            if any(
                self.can_assign_person_to_event(person_instance_id, event)
                for person_instance_id in usable_people
            ):
                actionable.append(event)
        return actionable

    def has_operational_options(self) -> bool:
        return bool(self.actionable_events())

    def ready_person_count(self) -> int:
        return len(self.usable_person_instance_ids())

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
        return self.default_equipment_target_for_slot("")

    def default_equipment_target_for_slot(self, equipment_slot: str) -> str | None:
        people = self.person_instance_ids()
        if not people:
            return None
        people_by_load = sorted(
            people,
            key=lambda instance_id: (
                self.equipped_item_for_slot(instance_id, equipment_slot) is not None
                if equipment_slot
                else False,
                len(self.equipment_for(instance_id)),
                self.catalog[self.collection[instance_id].card_id].name,
                instance_id,
            ),
        )
        for instance_id in people_by_load:
            if not equipment_slot or self.equipped_item_for_slot(instance_id, equipment_slot) is None:
                return instance_id
        return None

    def attach_equipment(
        self,
        equipment_instance_id: str,
        target_instance_id: str | None = None,
    ) -> None:
        equipment_instance = self.collection[equipment_instance_id]
        equipment_card = self.catalog[equipment_instance.card_id]
        if equipment_card.category != CardCategory.EQUIPMENT:
            raise ValueError("Only equipment cards can be attached.")

        resolved_target = target_instance_id or self.default_equipment_target_for_slot(
            equipment_card.equipment_slot,
        )
        if resolved_target is None:
            equipment_instance.equipped_to_instance_id = ""
            return
        if self.catalog[self.collection[resolved_target].card_id].category != CardCategory.PERSON:
            raise ValueError("Equipment can only be attached to a person card.")
        occupying_item = self.equipped_item_for_slot(resolved_target, equipment_card.equipment_slot)
        if occupying_item is not None and occupying_item.instance_id != equipment_instance_id:
            occupying_item.equipped_to_instance_id = ""
        equipment_instance.equipped_to_instance_id = resolved_target

    def normalize_equipment_assignments(self) -> None:
        valid_people = set(self.person_instance_ids())
        occupied_slots: set[tuple[str, str]] = set()
        for equipment_instance in sorted(
            (
                card_instance
                for card_instance in self.collection.values()
                if self.catalog[card_instance.card_id].category == CardCategory.EQUIPMENT
            ),
            key=lambda item: (self.catalog[item.card_id].name, item.instance_id),
        ):
            equipment_card = self.catalog[equipment_instance.card_id]
            slot_key = (
                equipment_instance.equipped_to_instance_id,
                equipment_card.equipment_slot,
            )
            if (
                equipment_instance.equipped_to_instance_id in valid_people
                and slot_key not in occupied_slots
            ):
                occupied_slots.add(slot_key)
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
        self.sanitize_piles()
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

    def sort_events(self) -> None:
        self.events.sort(
            key=lambda event: (
                event.deadline_day if event.deadline_day > 0 else self.day,
                EVENT_KIND_ORDER[event.kind],
                event.title,
                event.active_offer_id(),
            ),
        )

    def daily_templates(self) -> list[Event]:
        return [
            event
            for event in self.event_library.values()
            if event.is_daily()
        ]

    def incident_templates(self, source: str | None = None) -> list[Event]:
        templates = [
            event
            for event in self.event_library.values()
            if event.is_incident()
        ]
        if source is None:
            return templates
        return [event for event in templates if event.source == source]

    def special_templates(self) -> list[Event]:
        return sorted(
            (
                event
                for event in self.event_library.values()
                if event.is_special()
            ),
            key=lambda event: (event.storyline_id, event.chain_step, event.base_template_id()),
        )

    def _build_offer(self, template: Event, introduced_day: int | None = None) -> Event:
        start_day = introduced_day if introduced_day is not None else self.day
        return replace(
            template,
            template_id=template.base_template_id(),
            offer_id=self._next_offer_id(template.base_template_id()),
            introduced_day=start_day,
            deadline_day=start_day + max(template.deadline_days, 1) - 1,
        )

    def _has_active_template(self, template_id: str) -> bool:
        return any(event.base_template_id() == template_id for event in self.events)

    def _active_special_offer(self) -> Event | None:
        for event in self.events:
            if event.is_special():
                return event
        return None

    def refresh_day_board(self) -> None:
        self._expire_outdated_offers()
        if not self.is_won() and not self.is_lost():
            self._generate_daily_offers()
            self._maybe_add_random_incident()
            self._ensure_special_offer()
            self.sort_events()

    def _generate_daily_offers(self) -> None:
        current_daily = [event for event in self.events if event.is_daily()]
        if current_daily:
            return
        templates = self.daily_templates()
        if not templates:
            return
        sample_size = min(2, len(templates))
        for template in self.rng.sample(templates, sample_size):
            self.events.append(self._build_offer(template))

    def _maybe_add_random_incident(self) -> None:
        current_incident = [
            event
            for event in self.events
            if event.is_incident() and event.source != "tavern"
        ]
        if current_incident:
            return
        if self.rng.random() > INCIDENT_CHANCE:
            return
        templates = self.incident_templates(source="street")
        if not templates:
            return
        self.events.append(self._build_offer(self.rng.choice(templates)))

    def _ensure_special_offer(self) -> None:
        if self.special_chain_failed:
            return
        if self._active_special_offer() is not None:
            return
        chain = self.special_templates()
        if self.special_chain_progress >= len(chain):
            return
        self.events.append(self._build_offer(chain[self.special_chain_progress]))

    def _expire_outdated_offers(self) -> None:
        remaining_events: list[Event] = []
        for event in self.events:
            expired = False
            if event.is_daily() or event.is_incident():
                expired = event.introduced_day < self.day or event.deadline_day < self.day
            elif event.is_special():
                expired = event.deadline_day < self.day
            if not expired:
                remaining_events.append(event)
                continue
            if event.is_special():
                self.special_chain_failed = True
        self.events = remaining_events

    def _pay_weekly_tax(self) -> None:
        if self.day <= 1 or (self.day - 1) % 7 != 0:
            return
        if self.money >= self.weekly_tax_amount:
            self.money -= self.weekly_tax_amount
            return
        self.money = 0
        self.stability -= WEEKLY_TAX_STABILITY_PENALTY

    def _reserve_card_for_days(self, instance_id: str, days: int) -> None:
        if instance_id not in self.collection:
            return
        commitment = max(days, 1)
        card_instance = self.collection[instance_id]
        card_instance.busy_until_day = max(
            card_instance.busy_until_day,
            self.day + commitment - 1,
        )

    def _reserve_attached_equipment(self, person_instance_id: str, days: int) -> None:
        for equipment_instance in self.equipment_for(person_instance_id):
            self._reserve_card_for_days(equipment_instance.instance_id, days)

    def advance_day(self, recover_cards: bool = True) -> int:
        self.day += 1
        self.tavern_visits_today = 0
        self._pay_weekly_tax()
        self.refresh_day_board()
        self.sanitize_piles()
        return 1

    def advance_days(self, days: int, recover_cards: bool = True) -> int:
        days_advanced = 0
        for _ in range(max(days, 0)):
            days_advanced += self.advance_day(recover_cards=recover_cards)
        return days_advanced

    def end_day(self) -> int:
        return self.advance_day()

    def visit_tavern(self) -> Event | None:
        if self.tavern_visits_today >= 1:
            return None
        if self.money < TAVERN_VISIT_COST:
            return None
        templates = self.incident_templates(source="tavern")
        if not templates:
            return None
        self.money -= TAVERN_VISIT_COST
        template = self.rng.choice(templates)
        offer = self._build_offer(template)
        self.events.append(offer)
        self.tavern_visits_today = 1
        self.sort_events()
        return offer

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
        if not self.is_card_available(primary_instance_id):
            raise ValueError("That fixer is already committed to another job.")

        support_instance_id = None
        support_instance = None
        support_card = None
        if support_hand_index is not None:
            support_instance_id = self.hand[support_hand_index]
            support_instance = self.collection[support_instance_id]
            support_card = self.catalog[support_instance.card_id]
            if not support_card.is_general_info():
                raise ValueError("The support card must be a general info card.")
            if not self.is_card_available(support_instance_id):
                raise ValueError("That support card is already tied to another job.")

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

        self._reserve_card_for_days(primary_instance_id, event.time_cost)
        self._reserve_attached_equipment(primary_instance_id, event.time_cost)
        if support_instance_id is not None:
            self._reserve_card_for_days(support_instance_id, event.time_cost)

        self.events.pop(0)

        self.stability += resolution.stability_delta
        self.completed_events += 1

        money_delta = event.payout if resolution.success else 0
        self.money += money_delta

        if event.is_special():
            if resolution.success:
                self.special_chain_progress = max(self.special_chain_progress, event.chain_step)
            else:
                self.special_chain_failed = True

        if resolution.reward_card is not None:
            reward_instance = self.add_card_to_collection(resolution.reward_card.id)
            resolution = replace(resolution, reward_instance=reward_instance)

        self.sanitize_piles()
        self.sort_events()
        return replace(
            resolution,
            money_delta=money_delta,
            time_cost=event.time_cost,
            days_advanced=0,
        )

    def skip_event(self) -> Resolution:
        event = self.current_event()
        if event is None:
            raise ValueError("No event is available.")

        self.events.pop(0)
        message = "You put the offer aside for now."
        if event.is_special():
            self.events.append(event)
            self.sort_events()
            message = "You postponed the special request without dropping it."
        return Resolution(
            event=event,
            card=None,
            card_instance=None,
            success=False,
            score=0,
            stability_delta=0,
            reward_card=None,
            reward_instance=None,
            message=message,
            money_delta=0,
            time_cost=0,
            days_advanced=0,
        )

    def is_won(self) -> bool:
        chain = self.special_templates()
        return bool(chain) and self.special_chain_progress >= len(chain) and not self.special_chain_failed

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
                or f"{support_instance.display_name(support_card)} support pushed the check over the line."
            )
        else:
            message = event.success_text or "The assigned fixer cleared the check cleanly."
    elif event.required_card_ids and not has_required_info:
        required_names = ", ".join(
            catalog[card_id].name
            for card_id in event.required_card_ids
            if card_id in catalog
        )
        message = (
            f"Missing exclusive information [{required_names}] blocked the request."
            if required_names
            else "Missing exclusive information blocked the request."
        )
    else:
        message = (
            event.failure_text
            or f"The check total {check_total} fell short of the target {event.difficulty}."
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
    event_templates = build_story_events(db_path)
    return GameState(
        catalog=build_card_catalog(db_path),
        events=[],
        collection=build_starter_collection(db_path),
        rng=rng,
        event_library={event.base_template_id(): event for event in event_templates},
    )
