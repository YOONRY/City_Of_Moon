from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from random import Random

from moon_card_game.content import (
    build_card_catalog,
    build_starter_collection,
    build_story_events,
)
from moon_card_game.database import initialize_database
from moon_card_game.game import GameState, create_default_game, resolve_event
from moon_card_game.models import CardCategory
from moon_card_game.save_system import has_saved_game, load_game_state, save_game_state


class GameLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_content.sqlite3"
        initialize_database(self.db_path)
        self.catalog = build_card_catalog(self.db_path)
        self.events = build_story_events(self.db_path)
        self.starter_collection = build_starter_collection(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def assert_game_state_equal(self, left: GameState, right: GameState) -> None:
        self.assertEqual(left.stability, right.stability)
        self.assertEqual(left.completed_events, right.completed_events)
        self.assertEqual(left.hand, right.hand)
        self.assertEqual(left.draw_pile, right.draw_pile)
        self.assertEqual(left.discard_pile, right.discard_pile)
        self.assertEqual(
            [event.id for event in left.events],
            [event.id for event in right.events],
        )
        self.assertEqual(repr(left.rng.getstate()), repr(right.rng.getstate()))
        self.assertEqual(
            {
                instance_id: (
                    card_instance.card_id,
                    card_instance.power_bonus,
                    card_instance.current_durability,
                    card_instance.nickname,
                )
                for instance_id, card_instance in left.collection.items()
            },
            {
                instance_id: (
                    card_instance.card_id,
                    card_instance.power_bonus,
                    card_instance.current_durability,
                    card_instance.nickname,
                )
                for instance_id, card_instance in right.collection.items()
            },
        )

    def test_matching_card_succeeds_and_grants_reward(self) -> None:
        event = self.events[0]
        card_instance = self.starter_collection["starter_silver_tongue_1"]
        card = self.catalog[card_instance.card_id]

        resolution = resolve_event(event, card, card_instance, self.catalog)

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.reward_card.id, "merchant_seal")
        self.assertEqual(card_instance.effective_power(card), 3)
        self.assertGreaterEqual(resolution.stability_delta, 1)

    def test_non_matching_card_fails(self) -> None:
        event = self.events[1]
        card_instance = self.starter_collection["starter_back_alley_pass_1"]
        card = self.catalog[card_instance.card_id]

        resolution = resolve_event(event, card, card_instance, self.catalog)

        self.assertFalse(resolution.success)
        self.assertEqual(resolution.stability_delta, -1)

    def test_play_card_updates_collection_and_event_progress(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=self.events[:1],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            draw_pile=["starter_silver_tongue_1"],
            discard_pile=[],
            hand=[],
        )

        resolution = state.play_card(0)

        self.assertTrue(resolution.success)
        self.assertEqual(state.completed_events, 1)
        self.assertEqual(state.collection["starter_silver_tongue_1"].current_durability, 2)
        self.assertIsNotNone(resolution.reward_instance)
        self.assertIn(resolution.reward_instance.instance_id, state.collection)
        self.assertTrue(resolution.reward_instance.instance_id.startswith("merchant_seal_instance_"))

    def test_collection_groups_cards_by_category(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
        )

        grouped = state.collection_by_category()

        self.assertIn(CardCategory.DIPLOMACY, grouped)
        self.assertEqual(grouped[CardCategory.DIPLOMACY][0].card_id, "silver_tongue")

    def test_add_card_to_collection_creates_new_instance(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
        )

        new_instance = state.add_card_to_collection("silver_tongue", power_bonus=2)

        self.assertEqual(new_instance.power_bonus, 2)
        self.assertEqual(state.total_cards_owned(), 7)
        self.assertEqual(state.unique_cards_owned(), 6)

    def test_database_initializes_and_create_default_game_reads_instances(self) -> None:
        self.assertTrue(self.db_path.exists())

        state = create_default_game(seed=0, db_path=self.db_path)

        self.assertEqual(state.unique_cards_owned(), 6)
        self.assertEqual(state.total_cards_owned(), 6)
        self.assertEqual(state.current_event().id, "market_riot")
        self.assertEqual(state.collection["starter_silver_tongue_1"].power_bonus, 1)
        self.assertEqual(state.collection["starter_clockwork_drone_1"].current_durability, 2)

    def test_load_returns_none_when_slot_is_missing(self) -> None:
        self.assertFalse(has_saved_game(self.db_path, slot_name="missing"))
        self.assertIsNone(load_game_state(self.db_path, slot_name="missing"))

    def test_save_and_load_round_trip_preserves_run_state(self) -> None:
        original = create_default_game(seed=11, db_path=self.db_path)
        original.play_card(0)
        original.play_card(0)

        save_game_state(original, self.db_path, slot_name="checkpoint")
        self.assertTrue(has_saved_game(self.db_path, slot_name="checkpoint"))

        loaded = load_game_state(self.db_path, slot_name="checkpoint")

        self.assertIsNotNone(loaded)
        self.assert_game_state_equal(original, loaded)

        original.play_card(0)
        loaded.play_card(0)
        self.assert_game_state_equal(original, loaded)


if __name__ == "__main__":
    unittest.main()
