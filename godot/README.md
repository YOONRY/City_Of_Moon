# City of Moon Godot Pilot

이 폴더는 이제 웹 프로토타입을 대신해 본편 패키지로 옮겨 갈 Godot 프로젝트입니다.

현재 전략은 다음과 같습니다.

1. SQLite를 카드, 이벤트, 스타터 데이터의 원본으로 유지합니다.
2. Python에서 시작 런 스냅샷까지 포함한 `godot/data/content.json`을 export합니다.
3. Godot는 그 JSON을 읽어 실제 패키지용 화면과 흐름을 점진적으로 구축합니다.

## 데이터 갱신

저장소 루트에서:

```bash
python tools/export_godot_content.py
```

특정 SQLite 파일을 기준으로 export하려면:

```bash
python tools/export_godot_content.py --db-path .\moon_card_game\data\city_of_moon.sqlite3
```

`content.json`에는 다음이 포함됩니다.

- 전체 카드 정의
- 이벤트 템플릿
- 시작 시점 런 상태 미리보기(`previewState`)
  - 날짜, 자금, 안정도
  - 현재 열린 의뢰
  - 보유 카드 전체
  - 임무 중 여부와 남은 턴
  - 인물에 장착된 장비 정보

## 프로젝트 열기

1. Godot 4에서 프로젝트를 엽니다.
2. `godot` 폴더를 import합니다.
3. 메인 씬을 실행합니다.

현재 메인 씬은 다음을 확인하는 시작 런 프로토타입입니다.

- 실제 시작 런 기준 상태 바
- 현재 열린 의뢰 맵
- 선택한 의뢰의 판정/보상/슬롯 요구 정보
- 보유 카드 전체 레일
- 임무 중 카드 표시
- 인물 카드 선택 시 장착 장비 확인
- 주역/지원 카드 배치
- 의뢰 해결, 의뢰 넘기기, 술집 정보, 턴 종료
- `user://city_of_moon_save.json` 기준 저장/불러오기

이 단계의 목표는 콘텐츠를 많이 넣는 것이 아니라, Godot 쪽 게임 틀을 먼저 안정적으로 옮기는 것입니다.
