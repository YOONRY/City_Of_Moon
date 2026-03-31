PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    power INTEGER NOT NULL DEFAULT 1 CHECK (power >= 0),
    max_durability INTEGER NOT NULL DEFAULT 3 CHECK (max_durability > 0),
    rarity TEXT NOT NULL DEFAULT 'common'
);

CREATE TABLE IF NOT EXISTS card_tags (
    card_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (card_id, sort_order),
    UNIQUE (card_id, tag),
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    sort_order INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    success_delta INTEGER NOT NULL DEFAULT 1,
    failure_delta INTEGER NOT NULL DEFAULT -1,
    success_text TEXT NOT NULL DEFAULT '',
    failure_text TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS event_required_tags (
    event_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (event_id, sort_order),
    UNIQUE (event_id, tag),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_required_cards (
    event_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    card_id TEXT NOT NULL,
    PRIMARY KEY (event_id, sort_order),
    UNIQUE (event_id, card_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS event_bonus_tags (
    event_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (event_id, sort_order),
    UNIQUE (event_id, tag),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_rewards (
    event_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    card_id TEXT NOT NULL,
    PRIMARY KEY (event_id, sort_order),
    UNIQUE (event_id, card_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS starter_card_instances (
    instance_id TEXT PRIMARY KEY,
    sort_order INTEGER NOT NULL UNIQUE,
    card_id TEXT NOT NULL,
    power_bonus INTEGER NOT NULL DEFAULT 0,
    current_durability INTEGER NOT NULL CHECK (current_durability >= 0),
    nickname TEXT NOT NULL DEFAULT '',
    equipped_to_instance_id TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS save_slots (
    slot_name TEXT PRIMARY KEY,
    stability INTEGER NOT NULL,
    completed_events INTEGER NOT NULL,
    rng_state TEXT NOT NULL,
    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS save_card_instances (
    slot_name TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    power_bonus INTEGER NOT NULL DEFAULT 0,
    current_durability INTEGER NOT NULL CHECK (current_durability >= 0),
    nickname TEXT NOT NULL DEFAULT '',
    equipped_to_instance_id TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (slot_name, instance_id),
    FOREIGN KEY (slot_name) REFERENCES save_slots(slot_name) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS save_events (
    slot_name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    PRIMARY KEY (slot_name, sort_order),
    FOREIGN KEY (slot_name) REFERENCES save_slots(slot_name) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS save_piles (
    slot_name TEXT NOT NULL,
    pile_name TEXT NOT NULL CHECK (pile_name IN ('hand', 'draw', 'discard')),
    sort_order INTEGER NOT NULL,
    instance_id TEXT NOT NULL,
    PRIMARY KEY (slot_name, pile_name, sort_order),
    UNIQUE (slot_name, instance_id),
    FOREIGN KEY (slot_name) REFERENCES save_slots(slot_name) ON DELETE CASCADE,
    FOREIGN KEY (slot_name, instance_id)
        REFERENCES save_card_instances(slot_name, instance_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_card_tags_tag ON card_tags(tag);
CREATE INDEX IF NOT EXISTS idx_event_required_tags_tag ON event_required_tags(tag);
CREATE INDEX IF NOT EXISTS idx_event_required_cards_card ON event_required_cards(card_id);
CREATE INDEX IF NOT EXISTS idx_event_bonus_tags_tag ON event_bonus_tags(tag);
CREATE INDEX IF NOT EXISTS idx_save_events_slot ON save_events(slot_name);
CREATE INDEX IF NOT EXISTS idx_save_piles_slot ON save_piles(slot_name, pile_name);
