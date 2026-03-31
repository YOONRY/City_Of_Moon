from __future__ import annotations

import argparse

from moon_card_game import (
    CardDefinition,
    CardInstance,
    DEFAULT_SAVE_SLOT,
    GameState,
    create_default_game,
    has_saved_game,
    load_game_state,
    run_web_app,
    save_game_state,
)

CATEGORY_LABELS = {
    "person": "인물",
    "info": "정보",
    "equipment": "장비",
}
TAG_LABELS = {
    "route": "경로",
    "street": "거리",
    "negotiation": "교섭",
    "public": "공공",
    "shrine": "사당",
    "support": "지원",
    "covert": "잠입",
    "repair": "수리",
    "fixer": "해결",
    "survival": "생존",
    "escort": "호위",
    "combat": "전투",
    "medical": "치료",
    "evidence": "증거",
    "permit": "허가",
}
RARITY_LABELS = {
    "common": "일반",
    "uncommon": "고급",
    "rare": "희귀",
}


def format_tags(tags: tuple[str, ...]) -> str:
    return ", ".join(TAG_LABELS.get(tag, tag) for tag in tags)


def format_category(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def format_rarity(rarity: str) -> str:
    return RARITY_LABELS.get(rarity, rarity)


def format_instance_stats(
    game: GameState,
    card: CardDefinition,
    card_instance: CardInstance,
) -> str:
    equipment_bonus = (
        game.equipment_bonus_for(card_instance.instance_id)
        if card.category.value == "person"
        else 0
    )
    if card.category.value == "equipment":
        return f"보정 +{card_instance.effective_power(card)}"
    if equipment_bonus > 0:
        return (
            f"대응력 {game.effective_power(card_instance.instance_id)} "
            f"(기본 {card.power}{card_instance.power_bonus:+d}, 장비 +{equipment_bonus}) | "
            f"내구 {card_instance.current_durability}/{card.max_durability}"
        )
    return (
        f"대응력 {game.effective_power(card_instance.instance_id)} "
        f"(기본 {card.power}{card_instance.power_bonus:+d}) | "
        f"내구 {card_instance.current_durability}/{card.max_durability}"
    )


def equipment_note(game: GameState, instance_id: str) -> str:
    card = game.card_definition(instance_id)
    card_instance = game.card_instance(instance_id)
    if card.category.value == "equipment":
        if not card_instance.equipped_to_instance_id:
            return " | 장착 대상 없음"
        target_instance = game.card_instance(card_instance.equipped_to_instance_id)
        target_card = game.card_definition(card_instance.equipped_to_instance_id)
        return f" | 장착 대상: {target_instance.display_name(target_card)}"
    if card.category.value == "person":
        equipped_names = [
            equipment_instance.display_name(game.catalog[equipment_instance.card_id])
            for equipment_instance in game.equipment_for(instance_id)
        ]
        if equipped_names:
            return f" | 장착 장비: {', '.join(equipped_names)}"
    return ""


def print_intro() -> None:
    print("=" * 64)
    print("달의 도시 - 해결사 카드 프로토타입")
    print("=" * 64)
    print("도시의 해결사로서 의뢰와 사건을 처리하며 안정도를 지키세요.")
    print(
        "명령어: 숫자 = 카드 사용, info <n> = 카드 상세, "
        "collection = 소지 카드, save = 저장, "
        "load = 불러오기, skip = 넘기기, q = 종료"
    )
    print()


def print_collection(game: GameState) -> None:
    print("소지 카드")
    print(
        f"고유 카드: {game.unique_cards_owned()} | "
        f"총 인스턴스: {game.total_cards_owned()}"
    )
    for category, card_instances in game.collection_by_category().items():
        print(f"- {format_category(category.value)}")
        for card_instance in card_instances:
            card = game.catalog[card_instance.card_id]
            print(
                f"    {card_instance.display_name(card)} "
                f"[{card_instance.instance_id}] "
                f"({format_rarity(card.rarity)}) {format_instance_stats(game, card, card_instance)} "
                f"[{format_tags(card.tags)}]{equipment_note(game, card_instance.instance_id)}"
            )
    print()


def print_status(game: GameState) -> None:
    event = game.current_event()
    if event is None:
        return
    print("-" * 64)
    print(f"안정도: {game.stability} | 해결한 사건: {game.completed_events}")
    print(f"의뢰/사건: {event.title}")
    print(event.description)
    print(f"필수 태그: {format_tags(event.required_tags)}")
    if event.required_card_ids:
        required_names = ", ".join(game.catalog[card_id].name for card_id in event.required_card_ids)
        print(f"전용 정보: {required_names}")
    if event.bonus_tags:
        print(f"보너스 태그: {format_tags(event.bonus_tags)}")
    print()
    print("손패:")
    if not game.hand:
        print("  사용할 수 있는 카드가 없습니다. 'skip'으로 사건을 넘기세요.")
        print()
        return
    for index, instance_id in enumerate(game.hand, start=1):
        card_instance = game.card_instance(instance_id)
        card = game.card_definition(instance_id)
        print(
            f"  {index}. {card_instance.display_name(card)} "
            f"[{card_instance.instance_id}] "
            f"[{format_category(card.category.value)} | {format_tags(card.tags)}] "
            f"{format_instance_stats(game, card, card_instance)}"
            f"{equipment_note(game, instance_id)}"
        )
    print()


def print_card_detail(game: GameState, hand_index: int) -> None:
    instance_id = game.hand[hand_index]
    card_instance = game.card_instance(instance_id)
    card = game.card_definition(instance_id)
    print(
        f"{card_instance.display_name(card)} [{card_instance.instance_id}] "
        f"({format_rarity(card.rarity)})"
    )
    print(f"분류: {format_category(card.category.value)}")
    print(f"태그: {format_tags(card.tags)}")
    print(f"능력치: {format_instance_stats(game, card, card_instance)}")
    note = equipment_note(game, instance_id)
    if note:
        print(note.removeprefix(" | "))
    print(card.description)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="달의 도시 카드 프로토타입을 실행합니다.")
    parser.add_argument(
        "--ui",
        choices=("cli", "web"),
        default="cli",
        help="인터페이스 모드를 선택합니다. 그래픽 브라우저 UI는 'web'을 사용하세요.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="게임 콘텐츠 SQLite DB 파일 경로입니다.",
    )
    parser.add_argument(
        "--save-slot",
        default=DEFAULT_SAVE_SLOT,
        help="save/load 명령에 사용할 저장 슬롯 이름입니다.",
    )
    parser.add_argument(
        "--load-save",
        action="store_true",
        help="선택한 저장 슬롯이 있으면 불러와서 시작합니다.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="웹 UI 서버 호스트 주소입니다.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="웹 UI 서버 포트입니다.",
    )
    return parser.parse_args()


def game_loop(
    db_path: str | None = None,
    save_slot: str = DEFAULT_SAVE_SLOT,
    load_save: bool = False,
) -> None:
    save_exists = load_save and has_saved_game(db_path=db_path, slot_name=save_slot)
    game = (
        load_game_state(db_path=db_path, slot_name=save_slot)
        if save_exists
        else None
    )
    if game is None:
        game = create_default_game(db_path=db_path)
    print_intro()
    if load_save:
        if save_exists:
            print(f"'{save_slot}' 슬롯을 불러왔습니다.")
        else:
            print(f"'{save_slot}' 슬롯 저장이 없어 새 게임을 시작했습니다.")
        print()

    while not game.is_lost() and game.current_event() is not None:
        print_status(game)
        raw = input("카드를 선택하세요: ").strip()
        if not raw:
            continue
        lowered = raw.lower()
        if lowered == "q":
            print("게임을 종료했습니다.")
            return
        if lowered == "skip":
            resolution = game.skip_event()
            print(resolution.message)
            print(f"안정도 변화: {resolution.stability_delta:+d}")
            print()
            continue
        if lowered == "collection":
            print_collection(game)
            continue
        if lowered == "save":
            save_game_state(game, db_path=db_path, slot_name=save_slot)
            print(f"현재 진행을 '{save_slot}' 슬롯에 저장했습니다.")
            print()
            continue
        if lowered == "load":
            loaded_game = load_game_state(db_path=db_path, slot_name=save_slot)
            if loaded_game is None:
                print(f"'{save_slot}' 슬롯에 저장된 진행이 없습니다.")
            else:
                game = loaded_game
                print(f"'{save_slot}' 슬롯 저장을 불러왔습니다.")
            print()
            continue
        if lowered.startswith("info "):
            number = lowered.removeprefix("info ").strip()
            if not number.isdigit():
                print("'info <번호>' 형식으로 카드 상세를 확인하세요.")
                print()
                continue
            hand_index = int(number) - 1
            if hand_index < 0 or hand_index >= len(game.hand):
                print("그 번호의 카드는 손패에 없습니다.")
                print()
                continue
            print_card_detail(game, hand_index)
            continue
        if not lowered.isdigit():
            print(
                "카드 번호나 'info <n>', 'collection', "
                "'save', 'load', 'skip', 'q'를 입력하세요."
            )
            print()
            continue

        hand_index = int(lowered) - 1
        if hand_index < 0 or hand_index >= len(game.hand):
            print("그 번호의 카드는 손패에 없습니다.")
            print()
            continue

        resolution = game.play_card(hand_index)
        played_name = (
            resolution.card_instance.display_name(resolution.card)
            if resolution.card is not None and resolution.card_instance is not None
            else "카드 없음"
        )
        print(f"투입한 카드: {played_name}")
        print(resolution.message)
        print(f"결과: {'성공' if resolution.success else '실패'} | 점수 {resolution.score}")
        print(f"안정도 변화: {resolution.stability_delta:+d}")
        if resolution.card is not None and resolution.card_instance is not None:
            print(
                "카드 상태: "
                f"{format_instance_stats(game, resolution.card, resolution.card_instance)}"
            )
            if not resolution.card_instance.is_usable():
                print("이 카드는 더 이상 현장에 투입할 수 없습니다.")
        if resolution.reward_card is not None and resolution.reward_instance is not None:
            print(
                f"새 카드 획득: {resolution.reward_card.name} "
                f"[{resolution.reward_instance.instance_id}] "
                f"{format_instance_stats(game, resolution.reward_card, resolution.reward_instance)}"
                f"{equipment_note(game, resolution.reward_instance.instance_id)}"
            )
        print()

    if game.is_won():
        print("모든 의뢰를 처리했습니다. 해결사 사무소의 이름이 도시 전역에 퍼집니다.")
    else:
        print("도시의 안정이 무너졌습니다. 이번 의뢰선은 여기까지입니다.")
    print(f"해결한 사건: {game.completed_events}")
    print(f"모은 고유 카드: {game.unique_cards_owned()}")
    print(f"총 카드 인스턴스: {game.total_cards_owned()}")


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.ui == "web":
        run_web_app(
            db_path=arguments.db_path,
            save_slot=arguments.save_slot,
            load_save=arguments.load_save,
            host=arguments.host,
            port=arguments.port,
        )
    else:
        game_loop(
            db_path=arguments.db_path,
            save_slot=arguments.save_slot,
            load_save=arguments.load_save,
        )
