from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from moon_card_game.database import initialize_database
from moon_card_game.web_ui import GameSession, WEB_ROOT


class WebUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "web_ui.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_state_payload_includes_collection_events_and_run_state(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.state_payload()

        self.assertIn("collection", payload)
        self.assertIn("hand", payload)
        self.assertIn("events", payload)
        self.assertIn("day", payload)
        self.assertIn("money", payload)
        self.assertIn("readyPeople", payload)
        self.assertIn("canContinueDay", payload)
        self.assertIn("tavernCost", payload)
        self.assertTrue(all("busyUntilDay" in card for card in payload["collection"]))
        self.assertGreaterEqual(len(payload["collection"]), len(payload["hand"]))
        self.assertTrue(any(card["category"] == "equipment" for card in payload["collection"]))
        self.assertTrue(any(event["kind"] == "special" for event in payload["events"]))
        self.assertTrue(any(event["kind"] == "daily" for event in payload["events"]))
        self.assertTrue(all("stats" in card for card in payload["collection"]))
        self.assertTrue(all("checkStats" in event for event in payload["events"]))
        self.assertTrue(any(card["infoKind"] == "general" for card in payload["collection"]))
        self.assertTrue((WEB_ROOT / "index.html").exists())
        self.assertTrue((WEB_ROOT / "styles.css").exists())
        self.assertTrue((WEB_ROOT / "app.js").exists())

    def test_equipment_metadata_and_event_meta_are_serialized(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.state_payload()
        equipment_card = next(
            card for card in payload["collection"] if card["category"] == "equipment"
        )
        person_card = next(card for card in payload["collection"] if card["category"] == "person")
        general_info_card = next(
            card
            for card in payload["collection"]
            if card["category"] == "info" and card["infoKind"] == "general"
        )
        first_event = payload["events"][0]

        self.assertTrue(equipment_card["equippedToName"])
        self.assertIsInstance(person_card["attachedEquipmentNames"], list)
        self.assertIsInstance(person_card["attachedEquipment"], list)
        self.assertEqual(set(person_card["stats"].keys()), {"strength", "agility", "intelligence", "charm"})
        self.assertEqual(general_info_card["infoKind"], "general")
        self.assertIn("timeCost", first_event)
        self.assertIn("payout", first_event)
        self.assertIn("deadlineDay", first_event)
        self.assertIn("busyUntilDay", person_card)
        self.assertIn("busyTurnsRemaining", person_card)
        self.assertIn("equipmentSlot", equipment_card)

    def test_session_save_load_day_advance_and_tavern_round_trip(self) -> None:
        session = GameSession(db_path=self.db_path, save_slot="ui_slot")

        starting_money = session.state_payload()["money"]
        tavern_payload = session.visit_tavern()
        self.assertEqual(tavern_payload["money"], starting_money - tavern_payload["tavernCost"])
        played_payload = session.play_card(
            next(
                index
                for index, card in enumerate(session.state_payload()["hand"])
                if card["category"] == "person"
            )
        )

        self.assertEqual(played_payload["completedEvents"], 1)
        self.assertTrue(any(card["isCommitted"] for card in played_payload["collection"] if card["category"] == "person"))

        current_day = session.state_payload()["day"]
        end_day_payload = session.end_day()
        self.assertEqual(end_day_payload["day"], current_day + 1)

        session.save()
        session.new_game()
        self.assertEqual(session.state_payload()["day"], 1)

        loaded_payload = session.load()
        self.assertEqual(loaded_payload["day"], end_day_payload["day"])
        self.assertEqual(loaded_payload["saveSlot"], "ui_slot")

    def test_forfeit_marks_run_as_lost(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.forfeit()

        self.assertTrue(payload["isLost"])
        self.assertTrue(payload["isOver"])
        self.assertEqual(payload["stability"], 0)

    def test_empty_board_does_not_mark_run_as_over(self) -> None:
        session = GameSession(db_path=self.db_path)
        session.game.events = []

        payload = session.state_payload()

        self.assertFalse(payload["hasCurrentEvent"])
        self.assertFalse(payload["isOver"])


if __name__ == "__main__":
    unittest.main()
