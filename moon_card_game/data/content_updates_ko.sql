UPDATE cards SET
    name = '하층 지도 조각',
    category = 'info',
    info_kind = 'general',
    description = '하층 구역의 골목과 비밀 통로가 겹겹이 표시된 오래된 지도 조각.',
    strength = 0,
    agility = 1,
    intelligence = 3,
    charm = 0,
    max_durability = 2,
    rarity = 'common'
WHERE id = 'street_map';

UPDATE cards SET
    name = '교섭가 유나',
    category = 'person',
    info_kind = '',
    description = '도시의 이해관계를 읽고 갈등을 말로 풀어내는 해결사.',
    strength = 0,
    agility = 0,
    intelligence = 1,
    charm = 3,
    max_durability = 3,
    rarity = 'common'
WHERE id = 'silver_tongue';

UPDATE cards SET
    name = '사당 해석사 미라',
    category = 'person',
    info_kind = '',
    description = '사당 기록과 의식을 읽어 사건의 배경을 정리하는 조력자.',
    strength = 0,
    agility = 0,
    intelligence = 2,
    charm = 2,
    max_durability = 3,
    rarity = 'common'
WHERE id = 'moon_prayer';

UPDATE cards SET
    name = '뒷골목 연락원 타오',
    category = 'person',
    info_kind = '',
    description = '뒷골목 인맥과 잠입 실력으로 해결사의 발이 되어 주는 현장 인력.',
    strength = 0,
    agility = 3,
    intelligence = 1,
    charm = 0,
    max_durability = 3,
    rarity = 'common'
WHERE id = 'back_alley_pass';

UPDATE cards SET
    name = '태엽 정비사 렌',
    category = 'person',
    info_kind = '',
    description = '장치와 철로를 다루는 수리 담당 해결사.',
    strength = 1,
    agility = 0,
    intelligence = 2,
    charm = 0,
    max_durability = 3,
    rarity = 'common'
WHERE id = 'clockwork_drone';

UPDATE cards SET
    name = '야전 보급 가방',
    category = 'equipment',
    info_kind = '',
    description = '장기 의뢰를 버티게 해 주는 응급 보급과 간이 공구 묶음.',
    strength = 1,
    agility = 1,
    intelligence = 0,
    charm = 0,
    max_durability = 3,
    rarity = 'common'
WHERE id = 'field_rations';

UPDATE cards SET
    name = '가문의 검',
    category = 'equipment',
    info_kind = '',
    description = '위험한 의뢰에 투입되는 해결사에게 쥐여 주는 오래된 호신검.',
    strength = 2,
    agility = 1,
    intelligence = 0,
    charm = 0,
    max_durability = 4,
    rarity = 'uncommon'
WHERE id = 'heirloom_blade';

UPDATE cards SET
    name = '현장 처치 키트',
    category = 'equipment',
    info_kind = '',
    description = '부상자 응급 처치와 동행자 보호에 특화된 현장용 장비.',
    strength = 0,
    agility = 0,
    intelligence = 1,
    charm = 1,
    max_durability = 4,
    rarity = 'uncommon'
WHERE id = 'healer_kit';

UPDATE cards SET
    name = '월광 기록 렌즈',
    category = 'info',
    info_kind = 'general',
    description = '감춰진 흔적과 의식의 잔향을 읽어내는 조사용 렌즈 기록물.',
    strength = 0,
    agility = 0,
    intelligence = 3,
    charm = 1,
    max_durability = 2,
    rarity = 'uncommon'
WHERE id = 'oracle_lens';

UPDATE cards SET
    name = '상단 출입 인가서',
    category = 'info',
    info_kind = 'exclusive',
    description = '상류 구역과 상단 행사장에 드나들기 위한 정식 허가 문서.',
    strength = 0,
    agility = 0,
    intelligence = 1,
    charm = 4,
    max_durability = 2,
    rarity = 'uncommon'
WHERE id = 'merchant_seal';

UPDATE cards SET
    name = '철로 고정구',
    category = 'equipment',
    info_kind = '',
    description = '불안정한 철로와 문을 임시로 고정할 수 있는 개조 장비.',
    strength = 1,
    agility = 0,
    intelligence = 1,
    charm = 0,
    max_durability = 4,
    rarity = 'uncommon'
WHERE id = 'rail_spike';

UPDATE cards SET
    name = '안개의 가면',
    category = 'equipment',
    info_kind = '',
    description = '얼굴과 기척을 흐려 잠입 임무의 성공률을 높이는 보조 장비.',
    strength = 0,
    agility = 2,
    intelligence = 0,
    charm = 1,
    max_durability = 5,
    rarity = 'rare'
WHERE id = 'mask_of_mist';

DELETE FROM card_tags;

INSERT OR REPLACE INTO card_tags (card_id, sort_order, tag) VALUES
    ('street_map', 1, 'route'),
    ('street_map', 2, 'street'),
    ('silver_tongue', 1, 'negotiation'),
    ('silver_tongue', 2, 'public'),
    ('moon_prayer', 1, 'shrine'),
    ('moon_prayer', 2, 'support'),
    ('back_alley_pass', 1, 'covert'),
    ('back_alley_pass', 2, 'street'),
    ('clockwork_drone', 1, 'repair'),
    ('clockwork_drone', 2, 'fixer'),
    ('field_rations', 1, 'support'),
    ('field_rations', 2, 'survival'),
    ('heirloom_blade', 1, 'escort'),
    ('heirloom_blade', 2, 'combat'),
    ('healer_kit', 1, 'support'),
    ('healer_kit', 2, 'medical'),
    ('oracle_lens', 1, 'evidence'),
    ('oracle_lens', 2, 'shrine'),
    ('merchant_seal', 1, 'permit'),
    ('merchant_seal', 2, 'negotiation'),
    ('rail_spike', 1, 'repair'),
    ('rail_spike', 2, 'public'),
    ('mask_of_mist', 1, 'covert'),
    ('mask_of_mist', 2, 'escort');

UPDATE events SET
    title = '시장 중재 의뢰',
    description = '남부 시장에서 상단과 주민이 충돌 직전이다. 해결사 사무소로 급한 중재 의뢰가 들어왔다.',
    difficulty = 4,
    success_text = '말과 현장 대응이 통하며 시장은 간신히 안정을 되찾았다.',
    failure_text = '중재가 늦어지며 시장 불안이 도시 전체로 번졌다.'
WHERE id = 'market_riot';

UPDATE events SET
    title = '철로 긴급 수리',
    description = '외곽과 도심을 잇는 달 철로가 파손되어 물류와 인원이 발이 묶였다.',
    difficulty = 4,
    success_text = '철로를 임시 복구해 도시의 흐름을 다시 돌려놓았다.',
    failure_text = '철로 복구가 지연되며 시민들의 불만이 커졌다.'
WHERE id = 'broken_rail';

UPDATE events SET
    title = '가면무도회 잠입',
    description = '상류층 무도회에서 사라진 장부를 찾아 달라는 비밀 의뢰가 도착했다.',
    difficulty = 4,
    success_text = '행사장 안쪽 기록실에 잠입해 필요한 장부를 확보했다.',
    failure_text = '초대 절차에서 막혀 단서 없이 물러날 수밖에 없었다.'
WHERE id = 'masked_ball';

UPDATE events SET
    title = '월식 사당 이상 징후',
    description = '월식 직후 사당 기록 장치가 멈추고 담당자들이 불길한 소음을 들었다고 한다.',
    difficulty = 4,
    success_text = '사당 기록을 정리하고 현장을 안정시켜 추가 피해를 막았다.',
    failure_text = '이상 징후를 해석하지 못해 사당 일대에 불안이 남았다.'
WHERE id = 'eclipse_shrine';

UPDATE events SET
    title = '밀수 터널 추적',
    description = '뒷골목 조직이 지하 통로로 금지 물자를 옮긴다는 제보가 들어왔다.',
    difficulty = 4,
    success_text = '숨은 경로를 짚어내 밀수선을 끊고 조직의 움직임을 묶어 냈다.',
    failure_text = '통로를 놓치며 조직이 한발 앞서 달아났다.'
WHERE id = 'smuggler_tunnel';

UPDATE events SET
    title = '빙풍 속 호송 의뢰',
    description = '눈보라가 몰아치는 관문 밖에서 의뢰인이 구조와 동행을 요청하고 있다.',
    difficulty = 5,
    success_text = '혼란 속에서도 의뢰인을 지켜내며 관문까지 안전하게 데려왔다.',
    failure_text = '준비가 모자라 호송이 흔들렸고 관문 수비대의 신뢰를 잃었다.'
WHERE id = 'icewind_crossing';

DELETE FROM event_check_stats;

INSERT OR REPLACE INTO event_check_stats (event_id, sort_order, stat_name) VALUES
    ('market_riot', 1, 'charm'),
    ('market_riot', 2, 'intelligence'),
    ('broken_rail', 1, 'strength'),
    ('broken_rail', 2, 'intelligence'),
    ('masked_ball', 1, 'agility'),
    ('masked_ball', 2, 'charm'),
    ('eclipse_shrine', 1, 'intelligence'),
    ('eclipse_shrine', 2, 'charm'),
    ('smuggler_tunnel', 1, 'agility'),
    ('smuggler_tunnel', 2, 'intelligence'),
    ('icewind_crossing', 1, 'strength'),
    ('icewind_crossing', 2, 'charm');

DELETE FROM event_required_tags;

INSERT OR REPLACE INTO event_required_tags (event_id, sort_order, tag) VALUES
    ('market_riot', 1, 'negotiation'),
    ('market_riot', 2, 'public'),
    ('market_riot', 3, 'street'),
    ('broken_rail', 1, 'repair'),
    ('broken_rail', 2, 'route'),
    ('broken_rail', 3, 'public'),
    ('masked_ball', 1, 'covert'),
    ('masked_ball', 2, 'negotiation'),
    ('masked_ball', 3, 'permit'),
    ('eclipse_shrine', 1, 'shrine'),
    ('eclipse_shrine', 2, 'support'),
    ('eclipse_shrine', 3, 'repair'),
    ('smuggler_tunnel', 1, 'street'),
    ('smuggler_tunnel', 2, 'covert'),
    ('smuggler_tunnel', 3, 'route'),
    ('icewind_crossing', 1, 'support'),
    ('icewind_crossing', 2, 'public'),
    ('icewind_crossing', 3, 'fixer');

DELETE FROM event_required_cards;

INSERT OR REPLACE INTO event_required_cards (event_id, sort_order, card_id) VALUES
    ('masked_ball', 1, 'merchant_seal');

DELETE FROM event_bonus_tags;

INSERT OR REPLACE INTO event_bonus_tags (event_id, sort_order, tag) VALUES
    ('market_riot', 1, 'permit'),
    ('broken_rail', 1, 'fixer'),
    ('masked_ball', 1, 'street'),
    ('eclipse_shrine', 1, 'evidence'),
    ('smuggler_tunnel', 1, 'evidence'),
    ('icewind_crossing', 1, 'route');

DELETE FROM event_rewards;

INSERT OR REPLACE INTO event_rewards (event_id, sort_order, card_id) VALUES
    ('market_riot', 1, 'merchant_seal'),
    ('broken_rail', 1, 'rail_spike'),
    ('masked_ball', 1, 'mask_of_mist'),
    ('eclipse_shrine', 1, 'oracle_lens'),
    ('smuggler_tunnel', 1, 'heirloom_blade'),
    ('icewind_crossing', 1, 'healer_kit');

DELETE FROM starter_card_instances;

INSERT OR REPLACE INTO starter_card_instances (
    instance_id,
    sort_order,
    card_id,
    power_bonus,
    current_durability,
    nickname,
    equipped_to_instance_id
) VALUES
    ('starter_silver_tongue_1', 1, 'silver_tongue', 0, 3, '', ''),
    ('starter_moon_prayer_1', 2, 'moon_prayer', 0, 3, '', ''),
    ('starter_back_alley_pass_1', 3, 'back_alley_pass', 1, 3, '', ''),
    ('starter_clockwork_drone_1', 4, 'clockwork_drone', 0, 3, '', ''),
    ('starter_street_map_1', 5, 'street_map', 0, 2, '', ''),
    ('starter_field_rations_1', 6, 'field_rations', 0, 3, '', 'starter_clockwork_drone_1');
