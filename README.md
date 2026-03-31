# City of Moon

A small Python card game prototype built around a simple core loop:

- collect new cards while playing
- face story events one by one
- choose the card whose tags best match the event
- gain or lose city stability based on the outcome
- manage your collection by card category
- store game content in SQLite while runtime logic stays in Python objects
- track player-owned cards as individual instances with mutable stats

## Run

```bash
python main.py
```

On first run, the project creates a SQLite database automatically from the schema and seed files.

```bash
python main.py --db-path .\data\dev.sqlite3
```

To continue a saved run from the default slot:

```bash
python main.py --db-path .\data\dev.sqlite3 --load-save
```

## How it works

- Cards, tags, starter inventory, and story events live in SQLite.
- Python loads SQLite rows into `CardDefinition`, `CardInstance`, and `Event` objects before the game loop starts.
- Card definitions hold shared values such as base power and max durability.
- Player-owned card instances hold mutable values such as power bonus and current durability.
- The hand, draw pile, and discard pile all track `instance_id`, not just card type.
- The `save` and `load` commands store and restore the full run state in SQLite.
- Save data includes card instances, remaining events, pile order, stability, and RNG state.
- Each event asks for one or more tags.
- If the played card matches at least one required tag, the event succeeds.
- Bonus tags increase the reward.
- Successful events can add a brand-new card instance to your collection.
- In the console prototype, `collection` shows every owned instance and its current stats.

## Files

- `main.py`: console UI and input loop
- `moon_card_game/models.py`: data models for card definitions, card instances, and events
- `moon_card_game/database.py`: SQLite initialization, migration, and connection helpers
- `moon_card_game/content.py`: SQLite loaders that map rows into game objects
- `moon_card_game/data/schema.sql`: database schema
- `moon_card_game/data/seed.sql`: starter content inserted on first initialization
- `moon_card_game/game.py`: deck handling, instance state updates, and event resolution logic
- `moon_card_game/save_system.py`: save and load helpers for full run state
- `tests/test_game.py`: logic tests for the prototype

## Good next steps

- Add deck-building so players choose which owned instances go into the active deck
- Add branching story paths and multiple endings
- Add more mutable stats such as cooldown, corruption, or affinity
- Replace the console UI with `pygame` or another frontend
