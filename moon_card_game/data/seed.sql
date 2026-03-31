INSERT OR IGNORE INTO cards (id, name, category, description, power, max_durability, rarity) VALUES
    ('street_map', '거리 지도', 'investigation', '숨은 길과 우회로에 대한 메모가 빽빽이 적힌 손그림 지도.', 1, 3, 'common'),
    ('silver_tongue', '유려한 화술', 'diplomacy', '방 안의 긴장을 가라앉히고 귀족의 마음까지 흔드는 노련한 말솜씨.', 2, 3, 'common'),
    ('moon_prayer', '달의 기도', 'mystic', '두려움을 가라앉히고 길잡이를 불러들이는 낮은 속삭임의 기도.', 2, 3, 'common'),
    ('back_alley_pass', '뒷골목 통행증', 'stealth', '수상한 구역의 닫힌 문도 열게 만드는 호의의 증표.', 1, 3, 'common'),
    ('clockwork_drone', '태엽 드론', 'technology', '정찰과 수리를 위해 만들어진 작은 기계 동료.', 2, 3, 'common'),
    ('field_rations', '야전 식량', 'survival', '성벽 바깥의 긴 밤을 버티게 해 주는 든든한 보급품.', 1, 3, 'common'),
    ('heirloom_blade', '가문의 검', 'combat', '자부심보다 의무를 위해 차는 오래된 집안의 무기.', 2, 4, 'uncommon'),
    ('healer_kit', '치유 도구', 'support', '붕대와 약초, 그리고 위기 속에서도 흔들리지 않는 손.', 2, 4, 'uncommon'),
    ('oracle_lens', '신탁의 렌즈', 'investigation', '달빛이 숨기려 드는 진실까지 비춰내는 매끈한 렌즈.', 2, 4, 'uncommon'),
    ('merchant_seal', '상인 인장', 'diplomacy', '협상을 확실한 우위로 바꿔 주는 압인된 계약 인장.', 2, 4, 'uncommon'),
    ('rail_spike', '철로 스파이크', 'technology', '기관에도 비상 상황에도 쓸 수 있는 튼튼한 쇠말뚝.', 2, 4, 'uncommon'),
    ('mask_of_mist', '안개의 가면', 'stealth', '군중 속으로 몸을 감추게 해 주는 의식용 가면.', 3, 5, 'rare');

INSERT OR IGNORE INTO card_tags (card_id, sort_order, tag) VALUES
    ('street_map', 1, 'investigation'),
    ('street_map', 2, 'urban'),
    ('silver_tongue', 1, 'diplomacy'),
    ('silver_tongue', 2, 'noble'),
    ('moon_prayer', 1, 'mystic'),
    ('moon_prayer', 2, 'ritual'),
    ('back_alley_pass', 1, 'stealth'),
    ('back_alley_pass', 2, 'criminal'),
    ('clockwork_drone', 1, 'technology'),
    ('clockwork_drone', 2, 'repair'),
    ('field_rations', 1, 'survival'),
    ('field_rations', 2, 'trade'),
    ('heirloom_blade', 1, 'combat'),
    ('heirloom_blade', 2, 'honor'),
    ('healer_kit', 1, 'care'),
    ('healer_kit', 2, 'survival'),
    ('oracle_lens', 1, 'investigation'),
    ('oracle_lens', 2, 'mystic'),
    ('merchant_seal', 1, 'trade'),
    ('merchant_seal', 2, 'diplomacy'),
    ('rail_spike', 1, 'repair'),
    ('rail_spike', 2, 'combat'),
    ('mask_of_mist', 1, 'stealth'),
    ('mask_of_mist', 2, 'mystic');

INSERT OR IGNORE INTO events (id, sort_order, title, description, success_delta, failure_delta, success_text, failure_text) VALUES
    ('market_riot', 1, '시장 폭동', '달 시장의 거래 분쟁이 곧 폭력 사태로 번질 기세다.', 1, -1, '군중이 진정되고 시장 지도자들이 당신에게 빚을 진다.', '폭동이 번지고 도시가 당신을 신뢰하던 마음도 흔들린다.'),
    ('broken_rail', 2, '달 철로 파손', '상층 구역으로 향하는 철로가 끊겨 노동자들이 냉기 속에 발이 묶였다.', 1, -1, '구역이 얼어붙기 전에 철로를 복구해 냈다.', '수리가 지연되고 상층 구역은 그 책임을 당신에게 돌린다.'),
    ('masked_ball', 3, '가면무도회', '향수와 음악 뒤편에서 귀족들의 음모가 모습을 감춘다.', 1, -1, '비밀과 함께 새로운 초대장을 손에 넣고 무도회를 빠져나온다.', '너무 일찍 들켜 버렸고 궁정은 단단히 입을 닫는다.'),
    ('eclipse_shrine', 4, '월식 사당', '성스러운 의식 도중 사당의 달 거울에 금이 간다.', 1, -1, '의식이 회복되고 사당은 오래된 유물을 드러낸다.', '의식이 무너지고 구역 전체에 공황이 번져 간다.'),
    ('smuggler_tunnel', 5, '밀수꾼 터널', '항구 밑 숨겨진 터널에서 안개를 틈타 무기가 이동 중이다.', 1, -1, '밀수 경로를 드러내고 그들의 은닉 물자를 압수한다.', '밀수꾼들이 달아나고 항구는 더 위험한 곳이 된다.'),
    ('icewind_crossing', 6, '한풍 관문', '얼어붙는 폭풍이 닥치며 성문 밖의 순례자들이 고립되었다.', 1, -1, '순례자들을 무사히 데려와 도시의 감사를 얻는다.', '구조가 흔들리고 성문 구역의 분위기는 무겁게 가라앉는다.');

INSERT OR IGNORE INTO event_required_tags (event_id, sort_order, tag) VALUES
    ('market_riot', 1, 'diplomacy'),
    ('market_riot', 2, 'combat'),
    ('market_riot', 3, 'care'),
    ('broken_rail', 1, 'technology'),
    ('broken_rail', 2, 'repair'),
    ('broken_rail', 3, 'survival'),
    ('masked_ball', 1, 'stealth'),
    ('masked_ball', 2, 'diplomacy'),
    ('masked_ball', 3, 'investigation'),
    ('eclipse_shrine', 1, 'mystic'),
    ('eclipse_shrine', 2, 'ritual'),
    ('eclipse_shrine', 3, 'care'),
    ('smuggler_tunnel', 1, 'investigation'),
    ('smuggler_tunnel', 2, 'stealth'),
    ('smuggler_tunnel', 3, 'combat'),
    ('icewind_crossing', 1, 'survival'),
    ('icewind_crossing', 2, 'care'),
    ('icewind_crossing', 3, 'combat');

INSERT OR IGNORE INTO event_bonus_tags (event_id, sort_order, tag) VALUES
    ('market_riot', 1, 'trade'),
    ('market_riot', 2, 'honor'),
    ('broken_rail', 1, 'investigation'),
    ('masked_ball', 1, 'noble'),
    ('masked_ball', 2, 'mystic'),
    ('eclipse_shrine', 1, 'repair'),
    ('smuggler_tunnel', 1, 'criminal'),
    ('smuggler_tunnel', 2, 'technology'),
    ('icewind_crossing', 1, 'trade'),
    ('icewind_crossing', 2, 'honor');

INSERT OR IGNORE INTO event_rewards (event_id, sort_order, card_id) VALUES
    ('market_riot', 1, 'merchant_seal'),
    ('broken_rail', 1, 'rail_spike'),
    ('masked_ball', 1, 'mask_of_mist'),
    ('eclipse_shrine', 1, 'oracle_lens'),
    ('smuggler_tunnel', 1, 'heirloom_blade'),
    ('icewind_crossing', 1, 'healer_kit');

INSERT OR IGNORE INTO starter_card_instances (instance_id, sort_order, card_id, power_bonus, current_durability, nickname) VALUES
    ('starter_street_map_1', 1, 'street_map', 0, 3, ''),
    ('starter_silver_tongue_1', 2, 'silver_tongue', 1, 3, ''),
    ('starter_moon_prayer_1', 3, 'moon_prayer', 0, 3, ''),
    ('starter_back_alley_pass_1', 4, 'back_alley_pass', 0, 3, ''),
    ('starter_clockwork_drone_1', 5, 'clockwork_drone', 0, 2, ''),
    ('starter_field_rations_1', 6, 'field_rations', 0, 3, '');
