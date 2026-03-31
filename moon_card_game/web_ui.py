from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .game import GameState, create_default_game
from .models import CardCategory
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
    if card.category == CardCategory.PERSON:
        attached_equipment_names = [
            equipment_instance.display_name(game.catalog[equipment_instance.card_id])
            for equipment_instance in game.equipment_for(instance_id)
        ]

    return {
        "instanceId": card_instance.instance_id,
        "cardId": card.id,
        "name": card_instance.display_name(card),
        "category": card.category.value,
        "rarity": card.rarity,
        "tags": list(card.tags),
        "description": card.description,
        "basePower": card.power,
        "powerBonus": card_instance.power_bonus,
        "equipmentBonus": game.equipment_bonus_for(instance_id)
        if card.category == CardCategory.PERSON
        else 0,
        "power": game.effective_power(instance_id),
        "durability": card_instance.current_durability,
        "maxDurability": card.max_durability,
        "isUsable": card_instance.is_usable(),
        "isActiveCard": card.category != CardCategory.EQUIPMENT,
        "displayCategory": CATEGORY_LABELS.get(card.category.value, card.category.value),
        "equippedToInstanceId": card_instance.equipped_to_instance_id,
        "equippedToName": equipped_to_name,
        "attachedEquipmentNames": attached_equipment_names,
    }


def _serialize_event(game: GameState, index: int, event) -> dict[str, Any]:
    reward_names = [game.catalog[card_id].name for card_id in event.reward_card_ids]
    required_card_names = [game.catalog[card_id].name for card_id in event.required_card_ids]
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "requiredTags": list(event.required_tags),
        "requiredCardIds": list(event.required_card_ids),
        "requiredCardNames": required_card_names,
        "bonusTags": list(event.bonus_tags),
        "rewardNames": reward_names,
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
        "stability": game.stability,
        "completedEvents": game.completed_events,
        "uniqueCards": game.unique_cards_owned(),
        "totalInstances": game.total_cards_owned(),
        "isWon": game.is_won(),
        "isLost": game.is_lost(),
        "isOver": game.is_won() or game.is_lost() or game.current_event() is None,
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
            self.message = f"'{self.save_slot}' 슬롯을 불러왔습니다."
        elif load_save:
            self.message = f"'{self.save_slot}' 슬롯 저장이 없어 새 게임을 시작했습니다."
        else:
            self.message = "해결사 사무소로 새 의뢰가 도착했습니다. 적절한 카드로 사건을 처리하세요."

    def _make_game(self, load_save: bool) -> GameState:
        if load_save:
            saved_game = load_game_state(db_path=self.db_path, slot_name=self.save_slot)
            if saved_game is not None:
                return saved_game
        return create_default_game(db_path=self.db_path)

    def state_payload(self) -> dict[str, Any]:
        return serialize_game_state(self.game, self.message, self.save_slot)

    def play_card(self, hand_index: int) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            self.message = "이번 진행은 끝났습니다. 새 게임을 시작하거나 저장을 불러오세요."
            return self.state_payload()
        try:
            resolution = self.game.play_card(hand_index)
        except (IndexError, ValueError):
            self.message = "지금은 그 카드를 사용할 수 없습니다."
            return self.state_payload()

        played_name = (
            resolution.card_instance.display_name(resolution.card)
            if resolution.card is not None and resolution.card_instance is not None
            else "카드 없음"
        )
        result_text = "성공" if resolution.success else "실패"
        self.message = f"{played_name} 투입: {result_text}. {resolution.message}"
        if resolution.reward_card is not None:
            self.message += f" 새 카드 확보: {resolution.reward_card.name}."
        return self.state_payload()

    def skip_event(self) -> dict[str, Any]:
        if self.game.current_event() is None:
            self.message = "넘길 수 있는 사건이 없습니다."
            return self.state_payload()
        resolution = self.game.skip_event()
        self.message = f"이번 의뢰를 흘려보냈습니다. {resolution.message}"
        return self.state_payload()

    def save(self) -> dict[str, Any]:
        save_game_state(self.game, db_path=self.db_path, slot_name=self.save_slot)
        self.message = f"현재 진행을 '{self.save_slot}' 슬롯에 저장했습니다."
        return self.state_payload()

    def load(self) -> dict[str, Any]:
        saved_game = load_game_state(db_path=self.db_path, slot_name=self.save_slot)
        if saved_game is None:
            self.message = f"'{self.save_slot}' 슬롯에 저장된 진행이 없습니다."
            return self.state_payload()
        self.game = saved_game
        self.message = f"'{self.save_slot}' 슬롯을 불러왔습니다."
        return self.state_payload()

    def new_game(self) -> dict[str, Any]:
        self.game = create_default_game(db_path=self.db_path)
        self.message = "새로운 의뢰 목록이 열렸습니다. 해결사를 다시 배치해 보세요."
        return self.state_payload()

    def forfeit(self) -> dict[str, Any]:
        if self.game.is_won() or self.game.is_lost():
            self.message = "이 진행은 이미 종료되었습니다."
            return self.state_payload()
        self.game.stability = 0
        self.message = "이번 의뢰선을 포기했습니다. 도시의 신뢰가 크게 흔들렸습니다."
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
                self._send_json(session.play_card(hand_index))
                return
            if self.path == "/api/skip":
                self._send_json(session.skip_event())
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
    print(f"달의 도시 웹 UI 실행 중: http://{host}:{port}")
    print("브라우저에서 주소를 열어 주세요. 종료하려면 Ctrl+C를 누르세요.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
