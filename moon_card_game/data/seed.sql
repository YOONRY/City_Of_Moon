INSERT OR IGNORE INTO cards (id, name, category, description, power, max_durability, rarity) VALUES
    ('street_map', 'Street Map', 'investigation', 'A hand-drawn map packed with notes about hidden routes.', 1, 3, 'common'),
    ('silver_tongue', 'Silver Tongue', 'diplomacy', 'A practiced speech that can calm a room or sway a court.', 2, 3, 'common'),
    ('moon_prayer', 'Moon Prayer', 'mystic', 'A whispered rite that steadies fear and invites guidance.', 2, 3, 'common'),
    ('back_alley_pass', 'Back Alley Pass', 'stealth', 'A favor token that opens doors in less reputable districts.', 1, 3, 'common'),
    ('clockwork_drone', 'Clockwork Drone', 'technology', 'A tiny machine companion built for scouting and repairs.', 2, 3, 'common'),
    ('field_rations', 'Field Rations', 'survival', 'Reliable supplies for a hard night beyond the city walls.', 1, 3, 'common'),
    ('heirloom_blade', 'Heirloom Blade', 'combat', 'A family weapon carried more for duty than pride.', 2, 4, 'uncommon'),
    ('healer_kit', 'Healer Kit', 'support', 'Bandages, herbs, and a calm hand in a crisis.', 2, 4, 'uncommon'),
    ('oracle_lens', 'Oracle Lens', 'investigation', 'A polished lens that reveals what moonlight wants hidden.', 2, 4, 'uncommon'),
    ('merchant_seal', 'Merchant Seal', 'diplomacy', 'A stamped contract that turns negotiation into leverage.', 2, 4, 'uncommon'),
    ('rail_spike', 'Rail Spike', 'technology', 'A sturdy iron spike that works in engines and emergencies.', 2, 4, 'uncommon'),
    ('mask_of_mist', 'Mask of Mist', 'stealth', 'A ceremonial mask that lets you vanish into a crowd.', 3, 5, 'rare');

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
    ('market_riot', 1, 'Market Riot', 'A trade dispute in the moon market threatens to spill into violence.', 1, -1, 'The crowd steadies and the market leaders owe you a favor.', 'The riot spreads and the city''s trust in you slips.'),
    ('broken_rail', 2, 'Broken Lunar Rail', 'A rail line to the upper quarter snaps, stranding workers in the cold.', 1, -1, 'You restore the line before the district freezes over.', 'Repairs stall and the upper quarter blames your delay.'),
    ('masked_ball', 3, 'Masked Ball', 'A noble gathering hides a conspiracy behind music and perfume.', 1, -1, 'You leave the ball with secrets and a new invitation.', 'You are noticed too soon and the court closes ranks.'),
    ('eclipse_shrine', 4, 'Eclipse Shrine', 'The shrine''s moon mirror cracks during a sacred rite.', 1, -1, 'The rite recovers and the shrine reveals an ancient relic.', 'The rite collapses and panic echoes through the district.'),
    ('smuggler_tunnel', 5, 'Smuggler Tunnel', 'A hidden tunnel beneath the harbor is moving weapons under cover of fog.', 1, -1, 'You expose the route and seize the smugglers'' cache.', 'The smugglers escape and the harbor grows more dangerous.'),
    ('icewind_crossing', 6, 'Icewind Crossing', 'Pilgrims are trapped beyond the city gate as a freezing storm closes in.', 1, -1, 'You escort the pilgrims home and earn the city''s gratitude.', 'The rescue falters and the gate district turns grim.');

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
