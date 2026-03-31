UPDATE cards SET
    name = '거리 지도',
    description = '숨은 길과 우회로에 대한 메모가 빽빽이 적힌 손그림 지도.'
WHERE id = 'street_map';

UPDATE cards SET
    name = '유려한 화술',
    description = '방 안의 긴장을 가라앉히고 귀족의 마음까지 흔드는 노련한 말솜씨.'
WHERE id = 'silver_tongue';

UPDATE cards SET
    name = '달의 기도',
    description = '두려움을 가라앉히고 길잡이를 불러들이는 낮은 속삭임의 기도.'
WHERE id = 'moon_prayer';

UPDATE cards SET
    name = '뒷골목 통행증',
    description = '수상한 구역의 닫힌 문도 열게 만드는 호의의 증표.'
WHERE id = 'back_alley_pass';

UPDATE cards SET
    name = '태엽 드론',
    description = '정찰과 수리를 위해 만들어진 작은 기계 동료.'
WHERE id = 'clockwork_drone';

UPDATE cards SET
    name = '야전 식량',
    description = '성벽 바깥의 긴 밤을 버티게 해 주는 든든한 보급품.'
WHERE id = 'field_rations';

UPDATE cards SET
    name = '가문의 검',
    description = '자부심보다 의무를 위해 차는 오래된 집안의 무기.'
WHERE id = 'heirloom_blade';

UPDATE cards SET
    name = '치유 도구',
    description = '붕대와 약초, 그리고 위기 속에서도 흔들리지 않는 손.'
WHERE id = 'healer_kit';

UPDATE cards SET
    name = '신탁의 렌즈',
    description = '달빛이 숨기려 드는 진실까지 비춰내는 매끈한 렌즈.'
WHERE id = 'oracle_lens';

UPDATE cards SET
    name = '상인 인장',
    description = '협상을 확실한 우위로 바꿔 주는 압인된 계약 인장.'
WHERE id = 'merchant_seal';

UPDATE cards SET
    name = '철로 스파이크',
    description = '기관에도 비상 상황에도 쓸 수 있는 튼튼한 쇠말뚝.'
WHERE id = 'rail_spike';

UPDATE cards SET
    name = '안개의 가면',
    description = '군중 속으로 몸을 감추게 해 주는 의식용 가면.'
WHERE id = 'mask_of_mist';

UPDATE events SET
    title = '시장 폭동',
    description = '달 시장의 거래 분쟁이 곧 폭력 사태로 번질 기세다.',
    success_text = '군중이 진정되고 시장 지도자들이 당신에게 빚을 진다.',
    failure_text = '폭동이 번지고 도시가 당신을 신뢰하던 마음도 흔들린다.'
WHERE id = 'market_riot';

UPDATE events SET
    title = '달 철로 파손',
    description = '상층 구역으로 향하는 철로가 끊겨 노동자들이 냉기 속에 발이 묶였다.',
    success_text = '구역이 얼어붙기 전에 철로를 복구해 냈다.',
    failure_text = '수리가 지연되고 상층 구역은 그 책임을 당신에게 돌린다.'
WHERE id = 'broken_rail';

UPDATE events SET
    title = '가면무도회',
    description = '향수와 음악 뒤편에서 귀족들의 음모가 모습을 감춘다.',
    success_text = '비밀과 함께 새로운 초대장을 손에 넣고 무도회를 빠져나온다.',
    failure_text = '너무 일찍 들켜 버렸고 궁정은 단단히 입을 닫는다.'
WHERE id = 'masked_ball';

UPDATE events SET
    title = '월식 사당',
    description = '성스러운 의식 도중 사당의 달 거울에 금이 간다.',
    success_text = '의식이 회복되고 사당은 오래된 유물을 드러낸다.',
    failure_text = '의식이 무너지고 구역 전체에 공황이 번져 간다.'
WHERE id = 'eclipse_shrine';

UPDATE events SET
    title = '밀수꾼 터널',
    description = '항구 밑 숨겨진 터널에서 안개를 틈타 무기가 이동 중이다.',
    success_text = '밀수 경로를 드러내고 그들의 은닉 물자를 압수한다.',
    failure_text = '밀수꾼들이 달아나고 항구는 더 위험한 곳이 된다.'
WHERE id = 'smuggler_tunnel';

UPDATE events SET
    title = '한풍 관문',
    description = '얼어붙는 폭풍이 닥치며 성문 밖의 순례자들이 고립되었다.',
    success_text = '순례자들을 무사히 데려와 도시의 감사를 얻는다.',
    failure_text = '구조가 흔들리고 성문 구역의 분위기는 무겁게 가라앉는다.'
WHERE id = 'icewind_crossing';
