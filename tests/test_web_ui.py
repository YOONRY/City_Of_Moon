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

    def test_state_payload_includes_collection_and_event_requirements(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.state_payload()

        self.assertIn("collection", payload)
        self.assertIn("hand", payload)
        self.assertIn("events", payload)
        self.assertGreaterEqual(len(payload["collection"]), len(payload["hand"]))
        self.assertTrue(payload["events"][0]["isCurrent"])
        self.assertTrue(any(card["category"] == "equipment" for card in payload["collection"]))
        self.assertTrue(any(event["requiredCardNames"] for event in payload["events"]))
        self.assertTrue((WEB_ROOT / "index.html").exists())
        self.assertTrue((WEB_ROOT / "styles.css").exists())
        self.assertTrue((WEB_ROOT / "app.js").exists())

    def test_equipment_metadata_is_serialized(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.state_payload()
        equipment_card = next(
            card for card in payload["collection"] if card["category"] == "equipment"
        )
        person_card = next(card for card in payload["collection"] if card["category"] == "person")

        self.assertTrue(equipment_card["equippedToName"])
        self.assertIsInstance(person_card["attachedEquipmentNames"], list)

    def test_session_save_load_and_new_game_round_trip(self) -> None:
        session = GameSession(db_path=self.db_path, save_slot="ui_slot")

        first_event_id = session.state_payload()["events"][0]["id"]
        played_payload = session.play_card(0)

        self.assertEqual(played_payload["completedEvents"], 1)
        self.assertNotEqual(played_payload["events"][0]["id"], first_event_id)

        session.save()
        session.new_game()
        self.assertEqual(session.state_payload()["completedEvents"], 0)

        loaded_payload = session.load()
        self.assertEqual(loaded_payload["completedEvents"], 1)
        self.assertEqual(loaded_payload["saveSlot"], "ui_slot")

    def test_forfeit_marks_run_as_lost(self) -> None:
        session = GameSession(db_path=self.db_path)

        payload = session.forfeit()

        self.assertTrue(payload["isLost"])
        self.assertTrue(payload["isOver"])
        self.assertEqual(payload["stability"], 0)


if __name__ == "__main__":
    unittest.main()
