from __future__ import annotations

import argparse
from pathlib import Path

from moon_card_game import (
    DEFAULT_GODOT_EXPORT_PATH,
    export_godot_content,
    get_default_database_path,
    initialize_database,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="달의 도시 Godot 개발용 데이터 파이프라인을 실행합니다.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="콘텐츠 원본으로 사용할 SQLite DB 경로입니다.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Godot용 JSON 출력 경로입니다. 기본값은 godot/data/content.json 입니다.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="DB 초기화만 하고 Godot JSON export는 생략합니다.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    database_path = initialize_database(arguments.db_path)
    output_path = None if arguments.output is None else Path(arguments.output)

    print("=" * 64)
    print("달의 도시 - Godot 개발 파이프라인")
    print("=" * 64)
    print(f"SQLite 원본: {database_path}")

    if arguments.skip_export:
        print("Godot JSON export는 생략했습니다.")
    else:
        exported_path = export_godot_content(
            db_path=database_path,
            output_path=output_path,
        )
        print(f"Godot JSON export 완료: {exported_path}")

    print()
    print("다음 단계")
    print("1. Godot 4에서 godot 폴더를 프로젝트로 엽니다.")
    print("2. 메인 씬을 실행해 현재 런 상태와 의뢰 흐름을 확인합니다.")
    print("3. 데이터 변경 후에는 다시 `python main.py`로 export를 갱신합니다.")
    print()
    print(f"기본 DB 경로: {get_default_database_path()}")
    print(f"기본 Godot export 경로: {DEFAULT_GODOT_EXPORT_PATH}")


if __name__ == "__main__":
    main()
