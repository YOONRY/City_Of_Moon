from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .game import GameState, TAVERN_VISIT_COST, create_default_game
from .models import STAT_FIELDS, CardCategory
from .save_system import DEFAULT_SAVE_SLOT, has_saved_game, load_game_state, save_game_state

WEB_ROOT = Path(__file__).resolve().parent / "web"
CATEGORY_LABELS = {
    "person": "인물",
    "info": "정보",
    "equipment": "장비",
}


def _serialize_card(game: GameState, instance_id: str) -> dict[str, Any]:
    card_instance = game.card_instance(instance_id)
    card = game.card_definition(instance_id)
    equipped_to_name = ""
    if card.category == CardCategory.EQUIPMENT and card_instance.equipped_to_instance_id:
        target_instance = game.card_instance(card_instance.equipped_to_instance_id)
        target_card = game.card_definition(card_instance.equipped_to_instance_id)
        equipped_to_name = target_instance.display_name(target_card)

    attached_equipment_names = []
    attached_equipment = []
    if card.category == CardCategory.PERSON:
        for equipment_instance in game.equipment_for(instance_id):
            equipment_card = game.catalog[equipment_instance.card_id]
            equipment_name = equipment_instance.display_name(equipment_card)
            attached_equipment_names.append(equipment_name)
            attached_equipment.append(
                {
                    "instanceId": equipment_instance.instance_id,
                    "name": equipment_name,
                    "slot": equipment_card.equipment_slot,
                    "stats": equipment_instance.effective_stats(equipment_card),
                }
            )
    effective_stats = game.effective_stats(instance_id)
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
        "stats": effective_stats,
        "isUsable": game.is_card_available(instance_id),
        "isCommitted": card_instance.busy_until_day >= game.day,
        "busyUntilDay": card_instance.busy_until_day,
        "busyTurnsRemaining": busy_turns_remaining,
        "isActiveCard": card.category == CardCategory.PERSON or card.is_general_info(),
        "displayCategory": CATEGORY_LABELS.get(card.category.value, card.category.value),
        "equippedToInstanceId": card_instance.equipped_to_instance_id,
        "equippedToName": equipped_to_name,
        "attachedEquipmentNames": attached_equipment_names,
        "attachedEquipment": attached_equipment,
        "equipmentBonus": (
            game.equipment_bonus_for(instance_id)
            if card.category == CardCategory.PERSON
            else {stat_name: 0 for stat_name in STAT_FIELDS}
        ),
    }


def _serialize_event(game: GameState, index: int, event) -> dict[str, Any]:
    reward_names = [game.catalog[card_id].name for card_id in event.reward_card_ids]
    required_card_names = [game.catalog[card_id].name for card_id in event.required_card_ids]
    return {
        "id": event.id,
        "offerId": event.active_offer_id(),
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
        "rewardNames": reward_names,
        "timeCost": event.time_cost,
        "payout": event.payout,
        "deadlineDay": event.deadline_day,
        "isCurrent": index == 0,
    }


def serialize_game_state(
    game: GameState,
    message: str,
    save_slot: str,
) -> dict[str, Any]:
    collection = [
        _serialize_card(game, card_instance.instance_id)
        for card_instances in game.collection_by_category().values()
        for card_instance in card_instances
    ]
    hand_ids = set(game.hand)
    for card in collection:
        card["isInHand"] = card["instanceId"] in hand_ids
    return {
        "message": message,
        "saveSlot": save_slot,
        "day": game.day,
        "money": game.money,
        "tavernCost": TAVERN_VISIT_COST,
        "weeklyTaxAmount": game.weekly_tax_amount,
        "daysUntilTax": game.days_until_tax(),
        "stability": game.stability,
        "completedEvents": game.completed_events,
        "uniqueCards": game.unique_cards_owned(),
        "totalInstances": game.total_cards_owned(),
        "readyPeople": game.ready_person_count(),
        "canContinueDay": game.has_operational_options(),
        "isWon": game.is_won(),
        "isLost": game.is_lost(),
        "hasCurrentEvent": game.current_event() is not None,
        "isOver": game.is_won() or game.is_lost(),
        "hand": [_serialize_card(game, instance_id) for instance_id in game.hand],
        "collection": collection,
        "events": [
            _serialize_event(game, index, event)
            for index, event in enumerate(game.events)
        ],
    }


class GameSession:
    def __init__(
        self,
        db_path: str | Path | None = None,
        save_slot: str = DEFAULT_SAVE_SLOT,
        load_save: bool = False,
    ) -> None:
        self.db_path = db_path
        self.save_slot = save_slot
        self.game = self._make_game(load_save=load_save)
        if load_save and has_saved_game(db_path=self.db_path, slot_name=self.save_slot):
            self.message = f"Loaded save slot '{self.save_slot}'."
        elif load_save:
            self.message = f"No save found in '{self.save_slot}'. Started a new run."
        else:
            self.message = "A new fixer day begins. Choose a card and take a request."

    def _make_game(self, load_save: bool) -> GameState:
        if load_save:
            saved_game = load_game_state(db_path=self.db_path, slot_name=self.save_slot)
            if saved_game is not None:
                return saved_game
        return create_default_game(db_path=self.db_path)

    def state_payload(self) -> dict[str, Any]:
        return serialize_game_state(self.game, self.message, self.save_slot)

    def play_card(
        self,
        hand_index: int,
        support_hand_index: int | None = None,
    ) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            self.message = "This run has already ended. Start a new run or load a save."
            return self.state_payload()
        try:
            resolution = self.game.play_card(hand_index, support_hand_index=support_hand_index)
        except (IndexError, ValueError):
            self.message = "That card setup cannot be used right now."
            return self.state_payload()

        played_name = (
            resolution.card_instance.display_name(resolution.card)
            if resolution.card is not None and resolution.card_instance is not None
            else "No card"
        )
        result_text = "Success" if resolution.success else "Failure"
        self.message = f"{played_name}: {result_text}. {resolution.message}"
        if resolution.money_delta:
            self.message += f" Earned {resolution.money_delta} crowns."
        if resolution.reward_card is not None:
            self.message += f" Reward gained: {resolution.reward_card.name}."
        if resolution.days_advanced:
            self.message += f" Time moved forward by {resolution.days_advanced} day(s)."
        return self.state_payload()

    def skip_event(self) -> dict[str, Any]:
        if self.game.current_event() is None:
            self.message = "There is no request to set aside."
            return self.state_payload()
        resolution = self.game.skip_event()
        self.message = resolution.message
        return self.state_payload()

    def end_day(self) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            return self.state_payload()
        self.game.end_day()
        self.message = "The crew stands down and a new day begins."
        return self.state_payload()

    def visit_tavern(self) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            return self.state_payload()
        if self.game.tavern_visits_today >= 1:
            self.message = "You already worked the tavern for rumors today."
            return self.state_payload()
        if self.game.money < TAVERN_VISIT_COST:
            self.message = f"You need {TAVERN_VISIT_COST} crowns to work the tavern."
            return self.state_payload()
        offer = self.game.visit_tavern()
        if offer is None:
            self.message = "You cannot pull another tavern rumor right now."
        else:
            self.message = f"A tavern rumor uncovered '{offer.title}' for {TAVERN_VISIT_COST} crowns."
        return self.state_payload()

    def save(self) -> dict[str, Any]:
        save_game_state(self.game, db_path=self.db_path, slot_name=self.save_slot)
        self.message = f"Saved current progress to '{self.save_slot}'."
        return self.state_payload()

    def load(self) -> dict[str, Any]:
        saved_game = load_game_state(db_path=self.db_path, slot_name=self.save_slot)
        if saved_game is None:
            self.message = f"No saved run exists in '{self.save_slot}'."
            return self.state_payload()
        self.game = saved_game
        self.message = f"Loaded save slot '{self.save_slot}'."
        return self.state_payload()

    def new_game(self) -> dict[str, Any]:
        self.game = create_default_game(db_path=self.db_path)
        self.message = "Started a fresh fixer run."
        return self.state_payload()

    def forfeit(self) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            self.message = "This run is already over."
            return self.state_payload()
        self.game.stability = 0
        self.message = "You gave up the run. The city slips further out of reach."
        return self.state_payload()


def _build_handler(session: GameSession):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _serve_file(self, relative_path: str, content_type: str) -> None:
            file_path = WEB_ROOT / relative_path
            if not file_path.exists():
                self.send_error(404)
                return
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            body = self.rfile.read(length)
            return json.loads(body.decode("utf-8"))

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                self._serve_file("index.html", "text/html; charset=utf-8")
                return
            if self.path == "/styles.css":
                self._serve_file("styles.css", "text/css; charset=utf-8")
                return
            if self.path == "/app.js":
                self._serve_file("app.js", "application/javascript; charset=utf-8")
                return
            if self.path == "/api/state":
                self._send_json(session.state_payload())
                return
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            self.send_error(404)

        def do_POST(self) -> None:
            if self.path == "/api/play":
                data = self._read_json()
                try:
                    hand_index = int(data.get("handIndex", -1))
                except (TypeError, ValueError):
                    hand_index = -1
                try:
                    raw_support_index = data.get("supportHandIndex")
                    support_hand_index = (
                        int(raw_support_index)
                        if raw_support_index is not None
                        else None
                    )
                except (TypeError, ValueError):
                    support_hand_index = None
                self._send_json(session.play_card(hand_index, support_hand_index))
                return
            if self.path == "/api/skip":
                self._send_json(session.skip_event())
                return
            if self.path == "/api/end-day":
                self._send_json(session.end_day())
                return
            if self.path == "/api/tavern":
                self._send_json(session.visit_tavern())
                return
            if self.path == "/api/save":
                self._send_json(session.save())
                return
            if self.path == "/api/load":
                self._send_json(session.load())
                return
            if self.path == "/api/new":
                self._send_json(session.new_game())
                return
            if self.path == "/api/forfeit":
                self._send_json(session.forfeit())
                return
            self.send_error(404)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def run_web_app(
    db_path: str | Path | None = None,
    save_slot: str = DEFAULT_SAVE_SLOT,
    load_save: bool = False,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    session = GameSession(db_path=db_path, save_slot=save_slot, load_save=load_save)
    server = ThreadingHTTPServer((host, port), _build_handler(session))
    print(f"City of Moon web UI is running at http://{host}:{port}")
    print("Open the address in a browser. Press Ctrl+C to stop the local server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
