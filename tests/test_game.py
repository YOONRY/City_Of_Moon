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
from moon_card_game.game import (
    STARTING_MONEY,
    TAVERN_VISIT_COST,
    WEEKLY_TAX_AMOUNT,
    GameState,
    create_default_game,
    resolve_event,
)
from moon_card_game.models import CardCategory, CardInstance, EventKind
from moon_card_game.save_system import has_saved_game, load_game_state, save_game_state


class GameLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_content.sqlite3"
        initialize_database(self.db_path)
        self.catalog = build_card_catalog(self.db_path)
        self.templates = build_story_events(self.db_path)
        self.template_map = {event.base_template_id(): event for event in self.templates}
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
        self.assertEqual(left.day, right.day)
        self.assertEqual(left.money, right.money)
        self.assertEqual(left.stability, right.stability)
        self.assertEqual(left.completed_events, right.completed_events)
        self.assertEqual(left.special_chain_progress, right.special_chain_progress)
        self.assertEqual(left.special_chain_failed, right.special_chain_failed)
        self.assertEqual(left.offer_sequence, right.offer_sequence)
        self.assertEqual(left.tavern_visits_today, right.tavern_visits_today)
        self.assertEqual(left.hand, right.hand)
        self.assertEqual(left.draw_pile, right.draw_pile)
        self.assertEqual(left.discard_pile, right.discard_pile)
        self.assertEqual(
            [
                (
                    event.base_template_id(),
                    event.active_offer_id(),
                    event.introduced_day,
                    event.deadline_day,
                )
                for event in left.events
            ],
            [
                (
                    event.base_template_id(),
                    event.active_offer_id(),
                    event.introduced_day,
                    event.deadline_day,
                )
                for event in right.events
            ],
        )
        self.assertEqual(repr(left.rng.getstate()), repr(right.rng.getstate()))
        self.assertEqual(
            {
                instance_id: (
                    card_instance.card_id,
                    card_instance.power_bonus,
                    card_instance.nickname,
                    card_instance.equipped_to_instance_id,
                    card_instance.busy_until_day,
                )
                for instance_id, card_instance in left.collection.items()
            },
            {
                instance_id: (
                    card_instance.card_id,
                    card_instance.power_bonus,
                    card_instance.nickname,
                    card_instance.equipped_to_instance_id,
                    card_instance.busy_until_day,
                )
                for instance_id, card_instance in right.collection.items()
            },
        )

    def test_matching_person_card_succeeds_and_grants_reward(self) -> None:
        event = self.template_map["market_riot"]
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
        event = self.template_map["masked_ball"]
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
        self.assertIn("exclusive", resolution.message.lower())

    def test_required_info_allows_person_to_pass_stat_check(self) -> None:
        event = self.template_map["masked_ball"]
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
        event = self.template_map["broken_rail"]
        state = GameState(
            catalog=self.catalog,
            events=[event],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_draw_on_init=False,
            auto_plan_day_on_init=False,
        )

        resolution = state.play_card(
            state.hand.index("starter_clockwork_drone_1"),
            support_hand_index=state.hand.index("starter_street_map_1"),
        )

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.score, 7)
        self.assertEqual(resolution.money_delta, event.payout)
        self.assertEqual(state.collection["starter_clockwork_drone_1"].busy_until_day, 1)
        self.assertEqual(state.collection["starter_street_map_1"].busy_until_day, 1)
        self.assertEqual(state.collection["starter_field_rations_1"].busy_until_day, 1)
        self.assertFalse(state.is_card_available("starter_clockwork_drone_1"))
        self.assertEqual(state.day, 1)
        self.assertEqual(resolution.days_advanced, 0)

    def test_equipment_auto_equips_and_boosts_person_stats(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_plan_day_on_init=False,
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

    def test_hand_contains_all_owned_non_equipment_cards(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)

        cards_in_hand = [state.card_definition(instance_id) for instance_id in state.hand]
        categories = {card.category for card in cards_in_hand}

        self.assertNotIn(CardCategory.EQUIPMENT, categories)
        self.assertEqual(len(state.draw_pile), 0)
        self.assertEqual(len(state.discard_pile), 0)
        self.assertTrue(any(card.is_general_info() for card in cards_in_hand))
        self.assertEqual(len(state.hand), 5)

    def test_collection_groups_cards_by_new_categories(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_plan_day_on_init=False,
        )

        grouped = state.collection_by_category()

        self.assertIn(CardCategory.PERSON, grouped)
        self.assertIn(CardCategory.INFO, grouped)
        self.assertIn(CardCategory.EQUIPMENT, grouped)

    def test_create_default_game_starts_with_daily_board_and_story_request(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)

        daily_events = [event for event in state.events if event.kind == EventKind.DAILY]
        special_events = [event for event in state.events if event.kind == EventKind.SPECIAL]

        self.assertEqual(state.day, 1)
        self.assertEqual(state.money, STARTING_MONEY)
        self.assertEqual(state.ready_person_count(), 4)
        self.assertTrue(state.has_operational_options())
        self.assertEqual(len(daily_events), 2)
        self.assertEqual(len(special_events), 1)
        self.assertEqual(special_events[0].base_template_id(), "market_riot")
        self.assertEqual(state.unique_cards_owned(), 6)
        self.assertEqual(self.catalog["merchant_seal"].info_kind, "exclusive")
        self.assertEqual(self.catalog["street_map"].info_kind, "general")

    def test_end_day_refreshes_daily_contracts_and_releases_committed_cards(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)
        state.collection["starter_clockwork_drone_1"].busy_until_day = 1

        state.end_day()

        daily_events = [event for event in state.events if event.kind == EventKind.DAILY]
        self.assertEqual(state.day, 2)
        self.assertTrue(state.is_card_available("starter_clockwork_drone_1"))
        self.assertEqual(len(daily_events), 2)
        self.assertTrue(all(event.introduced_day == 2 for event in daily_events))
        self.assertTrue(all(event.deadline_day == 2 for event in daily_events))

    def test_weekly_tax_deducts_money_on_new_week(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)
        state.money = 20

        for _ in range(7):
            state.end_day()

        self.assertEqual(state.day, 8)
        self.assertEqual(state.money, 20 - WEEKLY_TAX_AMOUNT)

    def test_weekly_tax_penalizes_stability_when_money_is_short(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)
        state.money = 3
        state.stability = 3

        for _ in range(7):
            state.end_day()

        self.assertEqual(state.day, 8)
        self.assertEqual(state.money, 0)
        self.assertEqual(state.stability, 1)

    def test_tavern_visit_spawns_tavern_incident_and_costs_money(self) -> None:
        state = create_default_game(seed=0, db_path=self.db_path)

        offer = state.visit_tavern()

        self.assertIsNotNone(offer)
        self.assertEqual(offer.source, "tavern")
        self.assertTrue(any(event.source == "tavern" for event in state.events))
        self.assertEqual(state.tavern_visits_today, 1)
        self.assertEqual(state.money, STARTING_MONEY - TAVERN_VISIT_COST)
        self.assertIsNone(state.visit_tavern())

    def test_long_request_keeps_card_committed_without_advancing_day(self) -> None:
        event = self.template_map["market_riot"]
        state = GameState(
            catalog=self.catalog,
            events=[event],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_draw_on_init=False,
            auto_plan_day_on_init=False,
        )

        resolution = state.play_card(state.hand.index("starter_silver_tongue_1"))

        self.assertTrue(resolution.success)
        self.assertEqual(resolution.days_advanced, 0)
        self.assertEqual(state.day, 1)
        self.assertEqual(state.collection["starter_silver_tongue_1"].busy_until_day, 2)
        self.assertFalse(state.is_card_available("starter_silver_tongue_1"))

    def test_day_does_not_auto_end_when_no_operational_options_remain(self) -> None:
        first_event = self.template_map["daily_message_run"]
        second_event = self.template_map["daily_guild_ledger"]
        collection = {
            "solo_fixer": CardInstance(
                instance_id="solo_fixer",
                card_id="silver_tongue",
            )
        }
        state = GameState(
            catalog=self.catalog,
            events=[first_event, second_event],
            collection=collection,
            rng=Random(0),
            draw_pile=[],
            discard_pile=[],
            hand=["solo_fixer"],
            auto_draw_on_init=False,
            auto_plan_day_on_init=False,
        )

        resolution = state.play_card(0)

        self.assertEqual(resolution.days_advanced, 0)
        self.assertEqual(state.day, 1)
        self.assertEqual(state.collection["solo_fixer"].busy_until_day, 1)
        self.assertFalse(state.is_card_available("solo_fixer"))
        self.assertEqual(len(state.events), 1)
        self.assertFalse(state.has_operational_options())

        state.end_day()

        self.assertEqual(state.day, 2)
        self.assertTrue(state.is_card_available("solo_fixer"))

    def test_add_equipment_to_collection_attaches_to_person(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_plan_day_on_init=False,
        )

        new_instance = state.add_card_to_collection("heirloom_blade")

        self.assertEqual(self.catalog[new_instance.card_id].category, CardCategory.EQUIPMENT)
        self.assertTrue(new_instance.equipped_to_instance_id)
        self.assertEqual(state.total_cards_owned(), 7)
        self.assertEqual(state.unique_cards_owned(), 7)

    def test_same_equipment_slot_cannot_stack_on_one_person(self) -> None:
        state = GameState(
            catalog=self.catalog,
            events=[],
            collection=build_starter_collection(self.db_path),
            rng=Random(0),
            auto_plan_day_on_init=False,
        )

        first_weapon = state.add_card_to_collection(
            "heirloom_blade",
            equipped_to_instance_id="starter_silver_tongue_1",
        )
        second_weapon = state.add_card_to_collection(
            "rail_spike",
            equipped_to_instance_id="starter_silver_tongue_1",
        )

        self.assertEqual(second_weapon.equipped_to_instance_id, "starter_silver_tongue_1")
        self.assertEqual(first_weapon.equipped_to_instance_id, "")

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
        event_map = {event.base_template_id(): event for event in events}

        self.assertEqual(catalog["street_map"].name, "하층 지도 조각")
        self.assertEqual(catalog["street_map"].category, CardCategory.INFO)
        self.assertEqual(catalog["street_map"].info_kind, "general")
        self.assertEqual(event_map["market_riot"].title, "시장 중재 의뢰")

    def test_load_returns_none_when_slot_is_missing(self) -> None:
        self.assertFalse(has_saved_game(self.db_path, slot_name="missing"))
        self.assertIsNone(load_game_state(self.db_path, slot_name="missing"))

    def test_save_and_load_round_trip_preserves_run_state(self) -> None:
        original = create_default_game(seed=11, db_path=self.db_path)
        original.visit_tavern()
        original.play_card(self.first_person_hand_index(original))
        original.end_day()

        save_game_state(original, self.db_path, slot_name="checkpoint")
        self.assertTrue(has_saved_game(self.db_path, slot_name="checkpoint"))

        loaded = load_game_state(self.db_path, slot_name="checkpoint")

        self.assertIsNotNone(loaded)
        self.assert_game_state_equal(original, loaded)

        original.end_day()
        loaded.end_day()
        self.assert_game_state_equal(original, loaded)


if __name__ == "__main__":
    unittest.main()
