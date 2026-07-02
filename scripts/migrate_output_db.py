"""Create output.db, migrate battle data from pokemon.db, clean up."""
import sqlite3
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# 1. Create output.db
out = sqlite3.connect(str(DATA / "output.db"))
out.executescript("""
CREATE TABLE IF NOT EXISTS battle_pokemon_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL, turn INTEGER NOT NULL,
    side_index INTEGER NOT NULL, pokemon_index INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    hp INTEGER, max_hp INTEGER, hp_pct REAL,
    fainted INTEGER DEFAULT 0,
    ability_id INTEGER DEFAULT 0, item_id INTEGER DEFAULT 0,
    move_ids TEXT, slot INTEGER DEFAULT 0,
    UNIQUE(battle_id, turn, side_index, pokemon_index)
);
CREATE INDEX IF NOT EXISTS idx_ops_species ON battle_pokemon_states(species_id);
CREATE INDEX IF NOT EXISTS idx_ops_battle ON battle_pokemon_states(battle_id);
CREATE TABLE IF NOT EXISTS _imported_files (
    filepath TEXT PRIMARY KEY,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
out.commit()
print("output.db created")

# 2. Migrate data
src = sqlite3.connect(str(DATA / "pokemon.db"))
try:
    rows = src.execute("SELECT * FROM battle_pokemon_states").fetchall()
    if rows:
        cols = [c[1] for c in src.execute("PRAGMA table_info(battle_pokemon_states)").fetchall()]
        placeholders = ",".join(["?"] * len(cols))
        col_names = ",".join(cols)
        for r in rows:
            try:
                out.execute(f"INSERT OR IGNORE INTO battle_pokemon_states ({col_names}) VALUES ({placeholders})", r)
            except:
                pass
        out.commit()
        print(f"Migrated {len(rows)} battle rows")

    files = src.execute("SELECT * FROM _imported_files").fetchall()
    for f in files:
        try:
            out.execute("INSERT OR IGNORE INTO _imported_files(filepath,imported_at) VALUES (?,?)", f)
        except:
            pass
    out.commit()
    print(f"Migrated {len(files)} file records")

    # 3. Drop battle tables from pokemon.db
    src.execute("DROP TABLE IF EXISTS battle_pokemon_states")
    src.execute("DROP TABLE IF EXISTS _imported_files")
    src.commit()
    src.execute("VACUUM")
    print("Cleaned pokemon.db")
except Exception as e:
    print(f"Note: {e} (may already be migrated)")

out.close()
src.close()

# 4. Also ensure output_recent.db exists with same schema
recent = sqlite3.connect(str(DATA / "output_recent.db"))
recent.executescript("""
CREATE TABLE IF NOT EXISTS battle_pokemon_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL, turn INTEGER NOT NULL,
    side_index INTEGER NOT NULL, pokemon_index INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    hp INTEGER, max_hp INTEGER, hp_pct REAL,
    fainted INTEGER DEFAULT 0,
    ability_id INTEGER DEFAULT 0, item_id INTEGER DEFAULT 0,
    move_ids TEXT, slot INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(battle_id, turn, side_index, pokemon_index)
);
CREATE INDEX IF NOT EXISTS idx_rps_species ON battle_pokemon_states(species_id);
CREATE INDEX IF NOT EXISTS idx_rps_created ON battle_pokemon_states(created_at);
CREATE TABLE IF NOT EXISTS _imported_files (
    filepath TEXT PRIMARY KEY,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
recent.commit()
recent.close()
print("output_recent.db ready")

# 5. Verify
for name in ["pokemon", "output", "output_recent"]:
    conn = sqlite3.connect(str(DATA / f"{name}.db"))
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"{name}.db: {tables}")
    conn.close()
