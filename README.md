# 달의 도시 (City of Moon)

간단한 핵심 루프를 중심으로 만든 파이썬 카드 게임 프로토타입입니다.

- 플레이하며 새 카드를 수집합니다.
- 사건을 하나씩 마주하고 대응합니다.
- 사건 태그에 맞는 카드를 골라 사용합니다.
- 결과에 따라 도시 안정도가 오르거나 내려갑니다.
- 카드 카테고리별로 컬렉션을 관리합니다.
- 게임 원본 데이터는 SQLite에 두고, 실행 로직은 파이썬 객체로 다룹니다.
- 플레이어 소유 카드는 변동 스탯을 가진 개별 인스턴스로 추적합니다.
- 콘솔 UI와 브라우저 기반 그래픽 UI 둘 다 사용할 수 있습니다.

## 실행

```bash
python main.py
```

브라우저에서 그래픽 맵 UI를 열려면:

```bash
python main.py --ui web
```

처음 실행하면 스키마와 시드 파일을 바탕으로 SQLite 데이터베이스를 자동 생성합니다.

```bash
python main.py --db-path .\data\dev.sqlite3
```

기본 저장 슬롯에서 이어서 시작하려면:

```bash
python main.py --db-path .\data\dev.sqlite3 --load-save
```

웹 UI에서도 같은 옵션을 사용할 수 있습니다.

```bash
python main.py --ui web --db-path .\data\dev.sqlite3 --load-save --port 8765
```

## 동작 방식

- 카드, 태그, 시작 인벤토리, 사건 데이터는 SQLite에 저장됩니다.
- 파이썬은 SQLite 행을 `CardDefinition`, `CardInstance`, `Event` 객체로 읽어온 뒤 게임을 시작합니다.
- 카드 정의에는 기본 위력, 최대 내구도 같은 공용 수치가 들어갑니다.
- 플레이어 소유 카드 인스턴스에는 강화치, 현재 내구도 같은 변동 값이 들어갑니다.
- 손패, 드로우 더미, 버림 더미는 카드 종류가 아니라 `instance_id` 기준으로 관리됩니다.
- `save`와 `load` 명령은 전체 런 상태를 SQLite에 저장하고 복원합니다.
- 브라우저 UI는 상단에 사건 맵, 하단에 플레이 가능한 카드 레일을 보여줍니다.
- 저장 데이터에는 카드 인스턴스, 남은 사건, 더미 순서, 안정도, RNG 상태가 포함됩니다.
- 각 사건은 하나 이상의 태그를 요구합니다.
- 사용한 카드가 필수 태그 중 하나라도 맞으면 사건이 성공합니다.
- 보너스 태그가 맞으면 보상이 더 좋아집니다.
- 성공한 사건은 새 카드 인스턴스를 컬렉션에 추가할 수 있습니다.
- 콘솔 프로토타입에서는 `collection` 명령으로 보유 카드와 현재 스탯을 모두 볼 수 있습니다.

## 파일 구성

- `main.py`: 콘솔 루프와 웹 UI 서버를 함께 시작하는 진입점
- `moon_card_game/models.py`: 카드 정의, 카드 인스턴스, 사건 데이터 모델
- `moon_card_game/database.py`: SQLite 초기화, 마이그레이션, 연결 헬퍼
- `moon_card_game/content.py`: SQLite 행을 게임 객체로 바꾸는 로더
- `moon_card_game/data/schema.sql`: 데이터베이스 스키마
- `moon_card_game/data/seed.sql`: 첫 실행 시 들어가는 기본 데이터
- `moon_card_game/game.py`: 덱 처리, 카드 상태 변경, 사건 판정 로직
- `moon_card_game/save_system.py`: 전체 런 상태 저장/불러오기 헬퍼
- `moon_card_game/web_ui.py`: 로컬 HTTP 서버와 브라우저 UI용 JSON API
- `moon_card_game/web/`: 맵 스타일 인터페이스용 HTML, CSS, JavaScript
- `tests/test_game.py`: 핵심 게임 로직 테스트

## 다음 확장 아이디어

- 소유 카드 중 어떤 인스턴스를 덱에 넣을지 고르는 덱빌딩 추가
- 분기형 스토리와 여러 엔딩 추가
- 쿨다운, 오염, 친화도 같은 변동 스탯 추가
- 전용 일러스트, 맵 아이콘, 사운드로 웹 UI 연출 강화
