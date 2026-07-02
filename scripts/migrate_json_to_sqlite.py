#!/usr/bin/env python3
"""Migrate all data/*.json to data/pokemon.db (SQLite)."""
import json, sqlite3, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DB = DATA / "pokemon.db"

def main():
    if DB.exists(): DB.unlink()
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Run schema
    with open(DATA / "schema.sql") as f:
        conn.executescript(f.read())

    # ---- Species ----
    with open(DATA / "species.json") as f:
        species_list = json.load(f).get("species", [])
    for sp in species_list:
        stats = sp.get("baseStats", [0]*6)
        eggs = sp.get("eggGroups", ["", ""])
        conn.execute("""INSERT INTO species (id,name,type1,type2,base_hp,base_atk,base_def,
            base_spa,base_spd,base_spe,height,weight,male_ratio,evolution_level,
            next_evolution,egg_group1,egg_group2,hidden_ability)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            sp["id"], sp.get("name",""), sp.get("type1",""), sp.get("type2",""),
            stats[0] if len(stats)>0 else 0, stats[1] if len(stats)>1 else 0,
            stats[2] if len(stats)>2 else 0, stats[3] if len(stats)>3 else 0,
            stats[4] if len(stats)>4 else 0, stats[5] if len(stats)>5 else 0,
            sp.get("height",0), sp.get("weight",0), sp.get("maleRatio",0.5),
            sp.get("evolutionLevel",0), sp.get("nextEvolutionID",0),
            eggs[0] if len(eggs)>0 else "", eggs[1] if len(eggs)>1 else "",
            sp.get("hiddenAbilityID",0)))
    print(f"species: {conn.execute('SELECT COUNT(*) FROM species').fetchone()[0]} rows")

    # ---- Moves ----
    with open(DATA / "moves.json") as f:
        moves_list = json.load(f).get("moves", [])
    for mv in moves_list:
        conn.execute("""INSERT INTO moves (id,name,api_name,type,category,power,accuracy,
            pp,priority,target,effect,effect_chance,effect_param1,effect_param2,description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            mv["id"], mv.get("name",""), mv.get("apiName",""), mv.get("type","Normal"),
            mv.get("category","Status"), mv.get("power",0), mv.get("accuracy",100),
            mv.get("pp",0), mv.get("priority",0), mv.get("target","opponent"),
            str(mv.get("effect","")), mv.get("effectChance",0),
            mv.get("effectParam1",0), mv.get("effectParam2",0),
            mv.get("description","")))
    print(f"moves: {conn.execute('SELECT COUNT(*) FROM moves').fetchone()[0]} rows")

    # ---- Abilities ----
    with open(DATA / "abilities.json") as f:
        abilities_list = json.load(f).get("abilities", [])
    for ab in abilities_list:
        conn.execute("""INSERT INTO abilities (id,name,api_name,description)
            VALUES (?,?,?,?)""", (
            ab["id"], ab.get("name",""), ab.get("apiName",""),
            ab.get("description","")))
    print(f"abilities: {conn.execute('SELECT COUNT(*) FROM abilities').fetchone()[0]} rows")

    # ---- Items ----
    with open(DATA / "items.json") as f:
        items_list = json.load(f).get("items", [])
    for it in items_list:
        conn.execute("""INSERT INTO items (id,name,api_name,description,is_battle)
            VALUES (?,?,?,?,?)""", (
            it["id"], it.get("name",""), it.get("apiName",""),
            it.get("description",""), it.get("isBattle",1)))
    print(f"items: {conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]} rows")

    # ---- Learnsets ----
    with open(DATA / "learnsets.json") as f:
        learnsets = json.load(f)
    ls_count = 0
    for sid_str, moves in learnsets.items():
        sid = int(sid_str)
        for mid in moves:
            try:
                conn.execute("INSERT OR IGNORE INTO learnsets (species_id,move_id) VALUES (?,?)", (sid, mid))
                ls_count += 1
            except: pass
    print(f"learnsets: {conn.execute('SELECT COUNT(*) FROM learnsets').fetchone()[0]} rows ({ls_count} inserted)")

    # ---- Species-Abilities ----
    sa_count = 0
    for sp in species_list:
        for aid in sp.get("abilities", []):
            try:
                conn.execute("INSERT OR IGNORE INTO species_abilities (species_id,ability_id,is_hidden) VALUES (?,?,0)", (sp["id"], aid))
                sa_count += 1
            except: pass
        hid = sp.get("hiddenAbilityID", 0)
        if hid:
            try:
                conn.execute("INSERT OR IGNORE INTO species_abilities (species_id,ability_id,is_hidden) VALUES (?,?,1)", (sp["id"], hid))
                sa_count += 1
            except: pass
    print(f"species_abilities: {conn.execute('SELECT COUNT(*) FROM species_abilities').fetchone()[0]} rows ({sa_count} inserted)")

    conn.commit()

    # ---- Verify ----
    print(f"\n✅ Database: {DB} ({DB.stat().st_size / 1024 / 1024:.1f} MB)")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for (t,) in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} rows")

    # Speed test
    import time
    t0 = time.time()
    rows = conn.execute("SELECT s.name, s.type1, COUNT(l.move_id) as move_count FROM species s LEFT JOIN learnsets l ON s.id=l.species_id WHERE s.id=25 GROUP BY s.id").fetchall()
    t1 = time.time()
    print(f"\nQuery test: {rows[0]} ({((t1-t0)*1000):.1f}ms)")

    conn.close()

if __name__ == "__main__":
    main()
