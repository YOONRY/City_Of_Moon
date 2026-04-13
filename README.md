# 달의 도시 (City of Moon)

프로젝트 문의 세계관을 바탕으로 만든 팬게임형 카드 프로토타입입니다.  
플레이어는 도시의 해결사로서 의뢰를 받거나 예기치 않은 사건에 휘말리며, 상황에 맞는 카드를 골라 사건을 해결합니다.

현재 카드는 세 가지 축으로 나뉩니다.

- `인물 카드`: 현장에 직접 파견되는 해결사/조력자 카드
- `정보 카드`: 사건을 열거나 체크를 보조하는 정보 자산
- `장비 카드`: 인물 카드에 장착되어 대응력을 올려 주는 보조 자산

모든 카드는 `근력 / 민첩 / 지능 / 매력` 4가지 스탯을 가지며, 사건은 각자 정해진 체크 스탯과 목표치를 기준으로 판정됩니다.

정보 카드는 다시 두 종류로 나뉩니다.

- `전용 정보`: 특정 사건을 진행하기 위해 소지하고 있어야 하는 정보
- `범용 정보`: 손패에서 인물 카드와 함께 사용해 일시적으로 체크 수치를 올려 주는 정보

## 실행

현재 권장 경로는 Godot 프로젝트입니다.

루트에서 export를 갱신합니다.

```bash
python main.py
```

특정 DB를 기준으로 export하려면:

```bash
python main.py --db-path .\moon_card_game\data\city_of_moon.sqlite3
```

export 없이 DB만 초기화하려면:

```bash
python main.py --skip-export
```

그 다음 Godot 4에서 `godot` 폴더를 프로젝트로 열고 메인 씬을 실행하면 됩니다.  
자세한 흐름은 `godot/README.md`에 정리되어 있습니다.

## 현재 구조

- 카드 원본 데이터와 사건 데이터는 SQLite에 저장됩니다.
- 파이썬은 이를 `CardDefinition`, `CardInstance`, `Event` 객체로 읽어 게임을 구성합니다.
- `인물`과 `정보` 카드는 현재 보유 카드 전체를 기준으로 운용됩니다.
- `장비` 카드는 인물 카드에 장착되어 대응력을 보정합니다.
- `전용 정보`는 지원 슬롯이 아니라, 컬렉션에 소지하고 있는지만 검사합니다.
- 사건 성공 여부는 `인물 카드`의 체크 스탯 합과, 함께 사용한 `범용 정보`의 보조 스탯을 더한 값이 목표치를 넘는지로 결정됩니다.
- 저장 데이터에는 카드 인스턴스 상태, 장비 장착 상태, 남은 사건, 더미 순서, 안정도, RNG 상태가 포함됩니다.
- Godot 쪽은 export된 시작 런 스냅샷을 바탕으로 의뢰 해결, 턴 종료, 술집 정보, 저장/불러오기를 직접 처리합니다.

## 파일 구성

- `main.py`: Godot용 SQLite 초기화와 JSON export를 실행하는 진입점
- `moon_card_game/models.py`: 카드/사건 데이터 모델
- `moon_card_game/game.py`: 카드 판정, 장비 장착, 덱/손패 흐름
- `moon_card_game/database.py`: SQLite 초기화와 마이그레이션
- `moon_card_game/content.py`: SQLite 데이터를 게임 객체로 로드
- `moon_card_game/save_system.py`: 런 상태 저장/불러오기
- `moon_card_game/godot_export.py`: Godot용 JSON export 브리지
- `godot/`: 현재 주 개발 대상인 Godot 프로젝트
- `moon_card_game/data/schema.sql`: 데이터베이스 스키마
- `moon_card_game/data/seed.sql`: 기본 카드/사건 시드 데이터
- `tests/test_game.py`: 핵심 게임 로직 테스트
- `tests/test_godot_export.py`: Godot export 검증

## 다음 확장 아이디어

- 사건 화면을 `인물 슬롯 + 정보 슬롯` 구조로 확장
- 장비 장착/해제 UI를 추가해서 수동 편성 가능하게 만들기
- 해결사별 고유 능력치와 소속/성향 시스템 붙이기
- 의뢰 분기와 실패 누적에 따른 장기 스토리 변화 추가
