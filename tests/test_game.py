from __future__ import annotations

from pathlib import Path
from random import Random
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from moon_card_game.content import (
    build_card_catalog,
    build_starter_collection,
    build_story_events,
)
from moon_card_game.database import initialize_database
from moon_card_game.game import GameState, create_default_game, resolve_event
from moon_card_game.models import CardCategory, CardInstance
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

    @staticmethod
    def first_person_hand_index(game: GameState) -> int:
        return next(
            index
            for index, instance_id in enumerate(game.hand)
            if game.card_definition(instance_id).category == CardCategory.PERSON
        )

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
                    card_instance.equipped_to_instance_id,
                )
                for instance_id, card_instance in left.collection.items()
            },
            {
                instance_id: (
                    card_instance.card_id,
                    card_instance.power_bonus,
                    card_instance.current_durability,
                    card_instance.nickname,
                    card_instance.equipped_to_instance_id,
                )
                for instance_id, card_instance in right.collection.items()
            },
        )

    def test_matching_person_card_succeeds_and_grants_reward(self) -> None:
        event = self.events[0]
        card_instance = self.starter_collection["starter_silver_tongue_1"]
        card = self.catalog[card_instance.card_id]

        resolution = resolve_event(
            event,
            card,
            card_instance,
            self.catalog,
            effective_stats=card_instance.effective_stats(card),
        )

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.reward_card.id, "merchant_seal")
        self.assertEqual(resolution.score, 4)
        self.assertGreaterEqual(resolution.stability_delta, 1)

    def test_event_with_required_info_card_fails_without_specific_card(self) -> None:
        event = next(event for event in self.events if event.id == "masked_ball")
        card_instance = self.starter_collection["starter_back_alley_pass_1"]
        card = self.catalog[card_instance.card_id]

        resolution = resolve_event(
            event,
            card,
            card_instance,
            self.catalog,
            effective_stats=card_instance.effective_stats(card),
            has_required_info=False,
        )

        self.assertFalse(resolution.success)
        self.assertIn("전용 정보", resolution.message)

    def test_required_info_allows_person_to_pass_stat_check(self) -> None:
        event = next(event for event in self.events if event.id == "masked_ball")
        card_instance = self.starter_collection["starter_back_alley_pass_1"]
        card = self.catalog[card_instance.card_id]
        resolution = resolve_event(
            event,
            card,
            card_instance,
            self.catalog,
            effective_stats=card_instance.effective_stats(card),
            has_required_info=True,
        )

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.score, 4)

    def test_general_info_can_boost_person_temporarily(self) -> None:
        event = self.events[1]
        state = GameState(
            catalog=self.catalog,
            events=[event],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            draw_pile=[],
            discard_pile=[],
            hand=["starter_clockwork_drone_1", "starter_street_map_1"],
            auto_draw_on_init=False,
        )

        resolution = state.play_card(0, support_hand_index=1)

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.score, 7)
        self.assertEqual(state.collection["starter_street_map_1"].current_durability, 1)

    def test_equipment_auto_equips_and_boosts_person_power(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
        )

        self.assertEqual(
            state.collection["starter_field_rations_1"].equipped_to_instance_id,
            "starter_clockwork_drone_1",
        )
        self.assertEqual(
            state.equipment_bonus_for("starter_clockwork_drone_1"),
            {
                "strength": 1,
                "agility": 1,
                "intelligence": 0,
                "charm": 0,
            },
        )
        self.assertEqual(
            state.effective_stats("starter_clockwork_drone_1"),
            {
                "strength": 2,
                "agility": 1,
                "intelligence": 2,
                "charm": 0,
            },
        )

    def test_draw_pile_excludes_equipment_cards(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)

        cards_in_piles = [state.card_definition(instance_id) for instance_id in (state.hand + state.draw_pile + state.discard_pile)]
        categories = {card.category for card in cards_in_piles}

        self.assertNotIn(CardCategory.EQUIPMENT, categories)
        self.assertTrue(all(not card.is_exclusive_info() for card in cards_in_piles))

    def test_collection_groups_cards_by_new_categories(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
        )

        grouped = state.collection_by_category()

        self.assertIn(CardCategory.PERSON, grouped)
        self.assertIn(CardCategory.INFO, grouped)
        self.assertIn(CardCategory.EQUIPMENT, grouped)

    def test_add_equipment_to_collection_attaches_to_person(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
        )

        new_instance = state.add_card_to_collection("heirloom_blade")

        self.assertEqual(self.catalog[new_instance.card_id].category, CardCategory.EQUIPMENT)
        self.assertTrue(new_instance.equipped_to_instance_id)
        self.assertEqual(state.total_cards_owned(), 7)
        self.assertEqual(state.unique_cards_owned(), 7)

    def test_database_initializes_and_create_default_game_reads_instances(self) -> None:
        self.assertTrue(self.db_path.exists())

        state = create_default_game(seed=0, db_path=self.db_path)

        self.assertEqual(state.unique_cards_owned(), 6)
        self.assertEqual(state.total_cards_owned(), 6)
        self.assertEqual(state.current_event().id, "market_riot")
        self.assertEqual(state.collection["starter_back_alley_pass_1"].power_bonus, 1)
        self.assertEqual(self.catalog["merchant_seal"].info_kind, "exclusive")
        self.assertEqual(self.catalog["street_map"].info_kind, "general")
        self.assertEqual(
            state.collection["starter_field_rations_1"].equipped_to_instance_id,
            "starter_clockwork_drone_1",
        )

    def test_initialize_database_applies_updated_world_content(self) -> None:
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                "UPDATE cards SET name = ?, category = ?, info_kind = ? WHERE id = ?",
                ("Street Map", "investigation", "", "street_map"),
            )
            connection.execute(
                "UPDATE events SET title = ? WHERE id = ?",
                ("Market Riot", "market_riot"),
            )
            connection.commit()
        finally:
            connection.close()

        initialize_database(self.db_path)
        catalog = build_card_catalog(self.db_path)
        events = build_story_events(self.db_path)

        self.assertEqual(catalog["street_map"].name, "하층 지도 조각")
        self.assertEqual(catalog["street_map"].category, CardCategory.INFO)
        self.assertEqual(catalog["street_map"].info_kind, "general")
        self.assertEqual(events[0].title, "시장 중재 의뢰")

    def test_load_returns_none_when_slot_is_missing(self) -> None:
        self.assertFalse(has_saved_game(self.db_path, slot_name="missing"))
        self.assertIsNone(load_game_state(self.db_path, slot_name="missing"))

    def test_save_and_load_round_trip_preserves_run_state(self) -> None:
        original = create_default_game(seed=11, db_path=self.db_path)
        original.play_card(self.first_person_hand_index(original))
        original.play_card(self.first_person_hand_index(original))

        save_game_state(original, self.db_path, slot_name="checkpoint")
        self.assertTrue(has_saved_game(self.db_path, slot_name="checkpoint"))

        loaded = load_game_state(self.db_path, slot_name="checkpoint")

        self.assertIsNotNone(loaded)
        self.assert_game_state_equal(original, loaded)

        original.play_card(self.first_person_hand_index(original))
        loaded.play_card(self.first_person_hand_index(loaded))
        self.assert_game_state_equal(original, loaded)


if __name__ == "__main__":
    unittest.main()
