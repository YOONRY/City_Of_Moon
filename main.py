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
    save_game_state,
)


def format_tags(tags: tuple[str, ...]) -> str:
    return ", ".join(tags)


def format_category(category: str) -> str:
    return category.replace("_", " ").title()


def format_instance_stats(card: CardDefinition, card_instance: CardInstance) -> str:
    return (
        f"power {card_instance.effective_power(card)} "
        f"(base {card.power}{card_instance.power_bonus:+d}) | "
        f"durability {card_instance.current_durability}/{card.max_durability}"
    )


def print_intro() -> None:
    print("=" * 64)
    print("City of Moon - card event prototype")
    print("=" * 64)
    print("Collect cards, respond to city events, and protect stability.")
    print(
        "Commands: number = play card, info <n> = inspect card, "
        "collection = view cards, save = store progress, "
        "load = restore progress, skip = pass, q = quit"
    )
    print()


def print_collection(game: GameState) -> None:
    print("Collection")
    print(
        f"Unique cards: {game.unique_cards_owned()} | "
        f"Total instances: {game.total_cards_owned()}"
    )
    for category, card_instances in game.collection_by_category().items():
        print(f"- {format_category(category.value)}")
        for card_instance in card_instances:
            card = game.catalog[card_instance.card_id]
            print(
                f"    {card_instance.display_name(card)} "
                f"[{card_instance.instance_id}] "
                f"({card.rarity}) {format_instance_stats(card, card_instance)} "
                f"[{format_tags(card.tags)}]"
            )
    print()


def print_status(game: GameState) -> None:
    event = game.current_event()
    if event is None:
        return
    print("-" * 64)
    print(f"Stability: {game.stability} | Cleared events: {game.completed_events}")
    print(f"Event: {event.title}")
    print(event.description)
    print(f"Needed tags: {format_tags(event.required_tags)}")
    if event.bonus_tags:
        print(f"Bonus tags:  {format_tags(event.bonus_tags)}")
    print()
    print("Hand:")
    if not game.hand:
        print("  No usable cards left. Type 'skip' to pass the event.")
        print()
        return
    for index, instance_id in enumerate(game.hand, start=1):
        card_instance = game.card_instance(instance_id)
        card = game.card_definition(instance_id)
        print(
            f"  {index}. {card_instance.display_name(card)} "
            f"[{card_instance.instance_id}] "
            f"[{format_category(card.category.value)} | {format_tags(card.tags)}] "
            f"{format_instance_stats(card, card_instance)}"
        )
    print()


def print_card_detail(game: GameState, hand_index: int) -> None:
    instance_id = game.hand[hand_index]
    card_instance = game.card_instance(instance_id)
    card = game.card_definition(instance_id)
    print(f"{card_instance.display_name(card)} [{card_instance.instance_id}] ({card.rarity})")
    print(f"Category: {format_category(card.category.value)}")
    print(f"Tags: {format_tags(card.tags)}")
    print(f"Stats: {format_instance_stats(card, card_instance)}")
    print(card.description)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play the City of Moon card prototype.")
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional path to the SQLite database file for game content.",
    )
    parser.add_argument(
        "--save-slot",
        default=DEFAULT_SAVE_SLOT,
        help="Save slot name used by the save and load commands.",
    )
    parser.add_argument(
        "--load-save",
        action="store_true",
        help="Start by loading the selected save slot if it exists.",
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
            print(f"Loaded save slot '{save_slot}'.")
        else:
            print(f"No saved run found in slot '{save_slot}'. Started a new game.")
        print()

    while not game.is_lost() and game.current_event() is not None:
        print_status(game)
        raw = input("Choose a card: ").strip()
        if not raw:
            continue
        lowered = raw.lower()
        if lowered == "q":
            print("Game ended early.")
            return
        if lowered == "skip":
            resolution = game.skip_event()
            print(resolution.message)
            print(f"Stability change: {resolution.stability_delta:+d}")
            print()
            continue
        if lowered == "collection":
            print_collection(game)
            continue
        if lowered == "save":
            save_game_state(game, db_path=db_path, slot_name=save_slot)
            print(f"Saved current run to slot '{save_slot}'.")
            print()
            continue
        if lowered == "load":
            loaded_game = load_game_state(db_path=db_path, slot_name=save_slot)
            if loaded_game is None:
                print(f"No saved run found in slot '{save_slot}'.")
            else:
                game = loaded_game
                print(f"Loaded saved run from slot '{save_slot}'.")
            print()
            continue
        if lowered.startswith("info "):
            number = lowered.removeprefix("info ").strip()
            if not number.isdigit():
                print("Use 'info <number>' to inspect a card.")
                print()
                continue
            hand_index = int(number) - 1
            if hand_index < 0 or hand_index >= len(game.hand):
                print("That card number is not in your hand.")
                print()
                continue
            print_card_detail(game, hand_index)
            continue
        if not lowered.isdigit():
            print(
                "Enter a card number, 'info <n>', 'collection', "
                "'save', 'load', 'skip', or 'q'."
            )
            print()
            continue

        hand_index = int(lowered) - 1
        if hand_index < 0 or hand_index >= len(game.hand):
            print("That card number is not in your hand.")
            print()
            continue

        resolution = game.play_card(hand_index)
        played_name = (
            resolution.card_instance.display_name(resolution.card)
            if resolution.card is not None and resolution.card_instance is not None
            else "No card"
        )
        print(f"You played: {played_name}")
        print(resolution.message)
        print(f"Result: {'success' if resolution.success else 'failure'} | score {resolution.score}")
        print(f"Stability change: {resolution.stability_delta:+d}")
        if resolution.card is not None and resolution.card_instance is not None:
            print(
                "Card state: "
                f"{format_instance_stats(resolution.card, resolution.card_instance)}"
            )
            if not resolution.card_instance.is_usable():
                print("This card is worn out and will not return to the deck.")
        if resolution.reward_card is not None and resolution.reward_instance is not None:
            print(
                f"New card collected: {resolution.reward_card.name} "
                f"[{resolution.reward_instance.instance_id}] "
                f"{format_instance_stats(resolution.reward_card, resolution.reward_instance)}"
            )
        print()

    if game.is_won():
        print("The city endures. You finished the prototype story.")
    else:
        print("Stability fell to zero. The city slipped beyond your reach.")
    print(f"Events cleared: {game.completed_events}")
    print(f"Unique cards collected: {game.unique_cards_owned()}")
    print(f"Total card instances: {game.total_cards_owned()}")


if __name__ == "__main__":
    arguments = parse_args()
    game_loop(
        db_path=arguments.db_path,
        save_slot=arguments.save_slot,
        load_save=arguments.load_save,
    )
