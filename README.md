# 달의 도시 (City of Moon)

프로젝트 문의 세계관을 바탕으로 만든 팬게임형 카드 프로토타입입니다.  
플레이어는 도시의 해결사로서 의뢰를 받거나 예기치 않은 사건에 휘말리며, 상황에 맞는 카드를 골라 사건을 해결합니다.

현재 카드는 세 가지 축으로 나뉩니다.

- `인물 카드`: 현장에 직접 파견되는 해결사/조력자 카드
- `정보 카드`: 특정 사건의 실마리나 출입 허가, 조사 기록 같은 정보 자산
- `장비 카드`: 인물 카드에 장착되어 대응력을 올려 주는 보조 자산

## 실행

```bash
python main.py
```

브라우저 기반 UI를 열려면:

```bash
python main.py --ui web
```

처음 실행하면 스키마와 시드 데이터를 바탕으로 SQLite 데이터베이스를 자동 생성합니다.

```bash
python main.py --db-path .\data\dev.sqlite3
```

저장 슬롯에서 이어서 시작하려면:

```bash
python main.py --db-path .\data\dev.sqlite3 --load-save
```

웹 UI에서도 같은 옵션을 사용할 수 있습니다.

```bash
python main.py --ui web --db-path .\data\dev.sqlite3 --load-save --port 8765
```

## 현재 구조

- 카드 원본 데이터와 사건 데이터는 SQLite에 저장됩니다.
- 파이썬은 이를 `CardDefinition`, `CardInstance`, `Event` 객체로 읽어 게임을 구성합니다.
- `인물`과 `정보` 카드는 손패/드로우 더미에 들어가는 적극 카드입니다.
- `장비` 카드는 손패에 섞이지 않고 인물 카드에 장착되어 대응력을 보정합니다.
- 일부 사건은 태그뿐 아니라 전용 `정보 카드`가 있어야만 제대로 해결할 수 있습니다.
- 저장 데이터에는 카드 인스턴스 상태, 장비 장착 상태, 남은 사건, 더미 순서, 안정도, RNG 상태가 포함됩니다.

## 파일 구성

- `main.py`: 콘솔 루프와 웹 UI 서버를 시작하는 진입점
- `moon_card_game/models.py`: 카드/사건 데이터 모델
- `moon_card_game/game.py`: 카드 판정, 장비 장착, 덱/손패 흐름
- `moon_card_game/database.py`: SQLite 초기화와 마이그레이션
- `moon_card_game/content.py`: SQLite 데이터를 게임 객체로 로드
- `moon_card_game/save_system.py`: 런 상태 저장/불러오기
- `moon_card_game/web_ui.py`: 웹 UI용 로컬 HTTP 서버와 JSON API
- `moon_card_game/web/`: HTML, CSS, JavaScript UI 자산
- `moon_card_game/data/schema.sql`: 데이터베이스 스키마
- `moon_card_game/data/seed.sql`: 기본 카드/사건 시드 데이터
- `tests/test_game.py`: 핵심 게임 로직 테스트
- `tests/test_web_ui.py`: 웹 UI 직렬화 및 세션 테스트

## 다음 확장 아이디어

- 사건 화면을 `인물 슬롯 + 정보 슬롯` 구조로 확장
- 장비 장착/해제 UI를 추가해서 수동 편성 가능하게 만들기
- 해결사별 고유 능력치와 소속/성향 시스템 붙이기
- 의뢰 분기와 실패 누적에 따른 장기 스토리 변화 추가
