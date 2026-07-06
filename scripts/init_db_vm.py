import json, sqlite3, os
db = sqlite3.connect(os.path.expanduser("~/data/output.db"))
db.execute("CREATE TABLE IF NOT EXISTS battle_pokemon_states (id INTEGER PRIMARY KEY AUTOINCREMENT, battle_id TEXT NOT NULL, turn INTEGER DEFAULT 0, side_index INTEGER DEFAULT 0, pokemon_index INTEGER DEFAULT 0, species_id INTEGER DEFAULT 0, hp INTEGER DEFAULT 0, max_hp INTEGER DEFAULT 100, hp_pct REAL DEFAULT 0.0, fainted INTEGER DEFAULT 0, ability_id INTEGER DEFAULT 0, item_id INTEGER DEFAULT 0, move_ids TEXT DEFAULT '[]', slot INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))")
db.commit()
events = [json.loads(l) for l in open("event_new.jsonl", encoding="utf-8") if l.strip()]
total = 0
for e in events:
    if e["event"] != "battle_init":
        continue
    bid = e["data"]["battle_id"]
    for sk in ("a", "b"):
        idx = 0 if sk == "a" else 1
        team = e["data"].get(f"side_{sk}", [])
        for sl, mon in enumerate(team):
            db.execute("INSERT OR IGNORE INTO battle_pokemon_states VALUES (NULL,?,0,?,?,?,100,100,100.0,0,?,?,?,?,datetime('now'))", (bid, idx, sl, mon["speciesID"], mon.get("ability", 0), mon.get("item", 0), json.dumps(mon.get("moves", [])), sl))
            total += 1
db.commit()
db.close()
print(f"OK: {total} rows")
