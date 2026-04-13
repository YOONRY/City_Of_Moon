from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from .content import build_card_catalog, build_starter_collection, build_story_events
from .game import GameState, create_default_game
from .models import CardCategory, CardDefinition, CardInstance, Event, STAT_FIELDS

DEFAULT_GODOT_EXPORT_PATH = (
    Path(__file__).resolve().parent.parent / "godot" / "data" / "content.json"
)


def _card_payload(card: CardDefinition) -> dict[str, object]:
    return {
        "id": card.id,
        "name": card.name,
        "category": card.category.value,
        "equipmentSlot": card.equipment_slot,
        "infoKind": card.info_kind,
        "description": card.description,
        "tags": list(card.tags),
        "stats": card.stats(),
        "maxDurability": card.max_durability,
        "rarity": card.rarity,
    }


def _event_payload(
    event: Event,
    catalog: dict[str, CardDefinition],
) -> dict[str, object]:
    required_card_names = [
        catalog[card_id].name
        for card_id in event.required_card_ids
        if card_id in catalog
    ]
    reward_names = [
        catalog[card_id].name
        for card_id in event.reward_card_ids
        if card_id in catalog
    ]
    return {
        "id": event.id,
        "offerId": event.active_offer_id(),
        "templateId": event.base_template_id(),
        "title": event.title,
        "description": event.description,
        "kind": event.kind.value,
        "source": event.source,
        "checkStats": list(event.check_stats),
        "difficulty": event.difficulty,
        "requiredTags": list(event.required_tags),
        "requiredCardIds": list(event.required_card_ids),
        "requiredCardNames": required_card_names,
        "bonusTags": list(event.bonus_tags),
        "rewardCardIds": list(event.reward_card_ids),
        "rewardNames": reward_names,
        "personSlots": event.person_slots,
        "infoSlots": event.info_slots,
        "timeCost": event.time_cost,
        "payout": event.payout,
        "deadlineDays": event.deadline_days,
        "introducedDay": event.introduced_day,
        "deadlineDay": event.deadline_day,
        "storylineId": event.storyline_id,
        "chainStep": event.chain_step,
        "successDelta": event.success_delta,
        "failureDelta": event.failure_delta,
        "successText": event.success_text,
        "failureText": event.failure_text,
    }


def _starter_instance_payload(card_instance: CardInstance) -> dict[str, object]:
    return {
        "instanceId": card_instance.instance_id,
        "cardId": card_instance.card_id,
        "powerBonus": card_instance.power_bonus,
        "currentDurability": card_instance.current_durability,
        "nickname": card_instance.nickname,
        "equippedToInstanceId": card_instance.equipped_to_instance_id,
        "busyUntilDay": card_instance.busy_until_day,
    }


def _preview_card_payload(game: GameState, instance_id: str) -> dict[str, object]:
    card_instance = game.card_instance(instance_id)
    card = game.card_definition(instance_id)
    equipment_bonus = (
        game.equipment_bonus_for(instance_id)
        if card.category == CardCategory.PERSON
        else {stat_name: 0 for stat_name in STAT_FIELDS}
    )
    attached_equipment = []
    attached_equipment_names = []
    if card.category == CardCategory.PERSON:
        for equipment_instance in game.equipment_for(instance_id):
            equipment_card = game.catalog[equipment_instance.card_id]
            equipment_name = equipment_instance.display_name(equipment_card)
            attached_equipment_names.append(equipment_name)
            attached_equipment.append(
                {
                    "instanceId": equipment_instance.instance_id,
                    "cardId": equipment_card.id,
                    "name": equipment_name,
                    "slot": equipment_card.equipment_slot,
                    "stats": equipment_instance.effective_stats(equipment_card),
                }
            )

    equipped_to_name = ""
    if card.category == CardCategory.EQUIPMENT and card_instance.equipped_to_instance_id:
        target_instance = game.card_instance(card_instance.equipped_to_instance_id)
        target_card = game.card_definition(card_instance.equipped_to_instance_id)
        equipped_to_name = target_instance.display_name(target_card)

    busy_turns_remaining = max(card_instance.busy_until_day - game.day + 1, 0)
    return {
        "instanceId": card_instance.instance_id,
        "cardId": card.id,
        "name": card_instance.display_name(card),
        "category": card.category.value,
        "equipmentSlot": card.equipment_slot,
        "infoKind": card.info_kind,
        "rarity": card.rarity,
        "tags": list(card.tags),
        "description": card.description,
        "powerBonus": card_instance.power_bonus,
        "baseStats": card.stats(),
        "stats": game.effective_stats(instance_id),
        "isUsable": game.is_card_available(instance_id),
        "isCommitted": card_instance.busy_until_day >= game.day,
        "busyUntilDay": card_instance.busy_until_day,
        "busyTurnsRemaining": busy_turns_remaining,
        "isInHand": instance_id in set(game.hand),
        "equippedToInstanceId": card_instance.equipped_to_instance_id,
        "equippedToName": equipped_to_name,
        "attachedEquipmentNames": attached_equipment_names,
        "attachedEquipment": attached_equipment,
        "equipmentBonus": equipment_bonus,
    }


def _preview_state_payload(game: GameState) -> dict[str, object]:
    collection = [
        _preview_card_payload(game, card_instance.instance_id)
        for card_instances in game.collection_by_category().values()
        for card_instance in card_instances
    ]
    return {
        "day": game.day,
        "money": game.money,
        "stability": game.stability,
        "weeklyTaxAmount": game.weekly_tax_amount,
        "daysUntilTax": game.days_until_tax(),
        "completedEvents": game.completed_events,
        "uniqueCards": game.unique_cards_owned(),
        "totalInstances": game.total_cards_owned(),
        "readyPeople": game.ready_person_count(),
        "handOrder": list(game.hand),
        "collection": collection,
        "events": [_event_payload(event, game.catalog) for event in game.events],
    }


def build_godot_content_bundle(
    db_path: str | Path | None = None,
) -> dict[str, object]:
    catalog = build_card_catalog(db_path)
    event_templates = build_story_events(db_path)
    starter_collection = build_starter_collection(db_path)
    preview_state = create_default_game(seed=0, db_path=db_path)
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "schemaVersion": 2,
        "statOrder": list(STAT_FIELDS),
        "cards": [
            _card_payload(card)
            for _, card in sorted(catalog.items(), key=lambda item: item[0])
        ],
        "eventTemplates": [
            _event_payload(event, catalog)
            for event in event_templates
        ],
        "events": [
            _event_payload(event, catalog)
            for event in event_templates
        ],
        "starterCollection": [
            _starter_instance_payload(card_instance)
            for _, card_instance in sorted(
                starter_collection.items(),
                key=lambda item: item[0],
            )
        ],
        "previewState": _preview_state_payload(preview_state),
    }


def export_godot_content(
    db_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    destination = (
        Path(output_path)
        if output_path is not None
        else DEFAULT_GODOT_EXPORT_PATH
    ).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_godot_content_bundle(db_path)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
