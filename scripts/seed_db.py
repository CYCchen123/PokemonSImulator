#!/usr/bin/env python3
"""Populate SQLite database from data/*.json files."""
import json, sqlite3, sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "pokemon.db"

def main():
    # Remove old DB
    if DB_PATH.exists(): DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    # Run schema
    with open(DATA_DIR / "schema.sql") as f:
        conn.executescript(f.read())

    # ---- Load data ----
    def load(filename):
        with open(DATA_DIR / filename) as f:
            return json.load(f)

    species_data = load("species.json")
    species_list = species_data.get("species", species_data)
    moves_data = load("moves.json")
    moves_list = moves_data.get("moves", moves_data)
    abilities_data = load("abilities.json")
    abilities_list = abilities_data.get("abilities", abilities_data)
    items_data = load("items.json")
    items_list = items_data.get("items", items_data)

    print(f"Seeding: {len(species_list)} species, {len(moves_list)} moves, "
          f"{len(abilities_list)} abilities, {len(items_list)} items")

    # ---- Insert species ----
    for sp in species_list:
        types = sp.get("types", [sp.get("type1",""), sp.get("type2","")])
        stats = sp.get("baseStats", [0]*6)
        conn.execute("""INSERT INTO species (id,name,type1,type2,base_hp,base_atk,base_def,
            base_spa,base_spd,base_spe,height,weight,egg_group1,data_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            sp["id"], sp.get("name",""), types[0] if len(types)>0 else "",
            types[1] if len(types)>1 else "",
            stats[0] if len(stats)>0 else 0, stats[1] if len(stats)>1 else 0,
            stats[2] if len(stats)>2 else 0, stats[3] if len(stats)>3 else 0,
            stats[4] if len(stats)>4 else 0, stats[5] if len(stats)>5 else 0,
            sp.get("height",0), sp.get("weight",0),
            (sp.get("eggGroups",[""]) or [""])[0],
            json.dumps(sp, ensure_ascii=False)
        ))

    # ---- Insert moves ----
    for mv in moves_list:
        conn.execute("""INSERT INTO moves (id,name,type,category,power,accuracy,pp,priority,
            target,effect,effect_chance,description,data_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            mv["id"], mv.get("name", mv.get("apiName","")), mv.get("type",""),
            mv.get("category",""), mv.get("power",0), mv.get("accuracy",100),
            mv.get("pp",0), mv.get("priority",0), mv.get("target","opponent"),
            str(mv.get("effect","")), mv.get("effectChance",0),
            mv.get("description",""), json.dumps(mv, ensure_ascii=False)
        ))

    # ---- Insert abilities ----
    for ab in abilities_list:
        conn.execute("""INSERT INTO abilities (id,name,description,data_json)
            VALUES (?,?,?,?)""", (
            ab["id"], ab.get("name", ab.get("apiName","")),
            ab.get("description",""), json.dumps(ab, ensure_ascii=False)
        ))

    # ---- Insert items ----
    for it in items_list:
        conn.execute("""INSERT INTO items (id,name,description,is_battle,data_json)
            VALUES (?,?,?,?,?)""", (
            it["id"], it.get("name", it.get("apiName","")),
            it.get("description",""), it.get("isBattle",1),
            json.dumps(it, ensure_ascii=False)
        ))

    # ---- Junction: species_moves ----
    sm_count = 0
    for sp in species_list:
        for mid in sp.get("learnableMoves", []):
            conn.execute("""INSERT OR IGNORE INTO species_moves (species_id,move_id)
                VALUES (?,?)""", (sp["id"], mid))
            sm_count += 1

    # ---- Junction: species_abilities ----
    sa_count = 0
    for sp in species_list:
        for slot, aid in enumerate(sp.get("abilities", [])):
            conn.execute("""INSERT OR IGNORE INTO species_abilities (species_id,ability_id,slot)
                VALUES (?,?,?)""", (sp["id"], aid, slot+1))
            sa_count += 1
        hid = sp.get("hiddenAbilityID", 0)
        if hid:
            conn.execute("""INSERT OR IGNORE INTO species_abilities (species_id,ability_id,is_hidden,slot)
                VALUES (?,?,1,3)""", (sp["id"], hid))
            sa_count += 1

    conn.commit()

    # ---- Verify ----
    print(f"\n✅ Database seeded: {DB_PATH}")
    print(f"   species:          {conn.execute('SELECT COUNT(*) FROM species').fetchone()[0]}")
    print(f"   moves:            {conn.execute('SELECT COUNT(*) FROM moves').fetchone()[0]}")
    print(f"   abilities:        {conn.execute('SELECT COUNT(*) FROM abilities').fetchone()[0]}")
    print(f"   items:            {conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]}")
    print(f"   species_moves:    {conn.execute('SELECT COUNT(*) FROM species_moves').fetchone()[0]}")
    print(f"   species_abilities:{conn.execute('SELECT COUNT(*) FROM species_abilities').fetchone()[0]}")

    # Sample query
    row = conn.execute("""SELECT s.name, COUNT(sm.move_id) as move_count,
        GROUP_CONCAT(a.name, ', ') as abilities
        FROM species s
        JOIN species_moves sm ON s.id = sm.species_id
        JOIN species_abilities sa ON s.id = sa.species_id
        JOIN abilities a ON sa.ability_id = a.id
        WHERE s.id = 6
        GROUP BY s.id""").fetchone()
    if row:
        print(f"\n   Sample: {row[0]} → {row[1]} moves, abilities: {row[2]}")

    conn.close()

if __name__ == "__main__":
    main()
