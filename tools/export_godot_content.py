from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from moon_card_game.godot_export import export_godot_content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export SQLite-backed City of Moon content for the Godot pilot.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional SQLite database path to export from.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON output path. Defaults to godot/data/content.json.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    exported_path = export_godot_content(
        db_path=arguments.db_path,
        output_path=arguments.output,
    )
    print(f"Exported Godot content to {exported_path}")
