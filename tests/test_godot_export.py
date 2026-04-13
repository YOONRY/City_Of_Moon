from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from moon_card_game.database import initialize_database
from moon_card_game.godot_export import build_godot_content_bundle, export_godot_content


class GodotExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "godot_export.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_bundle_contains_cards_events_and_starter_collection(self) -> None:
        bundle = build_godot_content_bundle(self.db_path)

        self.assertEqual(bundle["schemaVersion"], 2)
        self.assertEqual(
            bundle["statOrder"],
            ["strength", "agility", "intelligence", "charm"],
        )
        self.assertTrue(bundle["cards"])
        self.assertTrue(bundle["eventTemplates"])
        self.assertTrue(bundle["starterCollection"])
        self.assertIn("previewState", bundle)

        merchant_seal = next(
            card for card in bundle["cards"] if card["id"] == "merchant_seal"
        )
        masked_ball = next(
            event for event in bundle["eventTemplates"] if event["id"] == "masked_ball"
        )
        preview_card = next(
            card
            for card in bundle["previewState"]["collection"]
            if card["instanceId"] == "starter_clockwork_drone_1"
        )

        self.assertEqual(merchant_seal["infoKind"], "exclusive")
        self.assertEqual(merchant_seal["equipmentSlot"], "")
        self.assertIn("merchant_seal", masked_ball["requiredCardIds"])
        self.assertGreaterEqual(masked_ball["personSlots"], 1)
        self.assertIn("busyUntilDay", bundle["starterCollection"][0])
        self.assertIn("attachedEquipment", preview_card)
        self.assertIn("equipmentBonus", preview_card)
        self.assertIn("events", bundle["previewState"])

    def test_export_writes_json_file_for_godot_project(self) -> None:
        output_path = Path(self.temp_dir.name) / "content.json"

        exported_path = export_godot_content(self.db_path, output_path)

        self.assertEqual(exported_path, output_path.resolve())
        self.assertTrue(exported_path.exists())

        payload = json.loads(exported_path.read_text(encoding="utf-8"))
        self.assertIn("generatedAt", payload)
        self.assertTrue(
            any(
                instance["instanceId"] == "starter_street_map_1"
                for instance in payload["starterCollection"]
            )
        )
        self.assertTrue(payload["previewState"]["events"])
        self.assertTrue(
            any(card["isInHand"] for card in payload["previewState"]["collection"])
        )

    def test_godot_project_scaffold_exists(self) -> None:
        workspace_root = Path(__file__).resolve().parents[1]

        self.assertTrue((workspace_root / "godot" / "project.godot").exists())
        self.assertTrue((workspace_root / "godot" / "scenes" / "main.tscn").exists())
        self.assertTrue((workspace_root / "godot" / "scripts" / "main.gd").exists())
        self.assertTrue((workspace_root / "godot" / "scripts" / "content_loader.gd").exists())


if __name__ == "__main__":
    unittest.main()
