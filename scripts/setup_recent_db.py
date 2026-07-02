"""Create the recent-hour database with same schema as historical."""
import sqlite3
from pathlib import Path

RECENT_DB = Path(__file__).resolve().parent.parent / "data" / "pokemon_recent.db"

conn = sqlite3.connect(str(RECENT_DB))
conn.executescript("""
CREATE TABLE IF NOT EXISTS battle_pokemon_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL,
    turn INTEGER NOT NULL,
    side_index INTEGER NOT NULL,
    pokemon_index INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    hp INTEGER, max_hp INTEGER, hp_pct REAL,
    fainted INTEGER DEFAULT 0,
    ability_id INTEGER DEFAULT 0,
    item_id INTEGER DEFAULT 0,
    move_ids TEXT,
    slot INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(battle_id, turn, side_index, pokemon_index)
);
CREATE INDEX IF NOT EXISTS idx_bps_species_r ON battle_pokemon_states(species_id);
CREATE INDEX IF NOT EXISTS idx_bps_created ON battle_pokemon_states(created_at);
CREATE TABLE IF NOT EXISTS _imported_files (
    filepath TEXT PRIMARY KEY,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()
conn.close()
print("Recent database ready.")
