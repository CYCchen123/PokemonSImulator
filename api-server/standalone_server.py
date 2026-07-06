from __future__ import annotations
"""
PokemonSimulator Standalone Server — WebSocket mode.
One WebSocket connection handles all communication (battles, data, matchmaking).
"""
import asyncio, json, os, uuid, subprocess, tempfile, shutil, logging, threading
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from analytics_service import (
    get_meta_species, get_meta_moves, get_meta_items, get_meta_abilities,
    get_type_distribution, get_battle_hp_curve, get_event_distribution,
    get_battle_survival, get_deep_stats_package, get_analysis_summary,
    get_pokemon_hp, get_species_detail,
    get_team_synergy, get_head_to_head,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ws] %(levelname)s: %(message)s')
logger = logging.getLogger("ws-server")

app = FastAPI(title="PokemonSimulator WebSocket API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_BIN = PROJECT_ROOT / "build" / "PokemonSimulator"
DATA_DIR = PROJECT_ROOT / "data"

# ============================================================
# Game Data Cache
# ============================================================
_species: dict = {}
_moves: dict = {}
_abilities: dict = {}
_items: dict = {}

def load_all_data():
    """Load all game data from SQLite (fast, indexed queries)."""
    global _species, _moves, _abilities, _items
    import sqlite3
    db_path = DATA_DIR / "pokemon.db"
    if not db_path.exists():
        logger.warning("pokemon.db not found, run: python3 scripts/migrate_json_to_sqlite.py")
        return
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Species
    for row in conn.execute("SELECT * FROM species"):
        _species[row["id"]] = {
            "id": row["id"], "name": row["name"],
            "types": [row["type1"], row["type2"] if row["type2"] else ""],
            "baseStats": [row["base_hp"], row["base_atk"], row["base_def"],
                          row["base_spa"], row["base_spd"], row["base_spe"]],
            "abilities": [], "hiddenAbilityID": row["hidden_ability"],
            "learnableMoves": []}

    # Species abilities
    for row in conn.execute("SELECT * FROM species_abilities"):
        sid = row["species_id"]
        if sid in _species:
            if row["is_hidden"]:
                _species[sid]["hiddenAbilityID"] = row["ability_id"]
            else:
                _species[sid]["abilities"].append(row["ability_id"])

    # Learnsets
    for row in conn.execute("SELECT species_id, move_id FROM learnsets ORDER BY species_id, move_id"):
        sid = row["species_id"]
        if sid in _species:
            _species[sid]["learnableMoves"].append(row["move_id"])

    # Moves
    for row in conn.execute("SELECT * FROM moves"):
        _moves[row["id"]] = {"id": row["id"], "name": row["name"],
            "type": row["type"], "category": row["category"],
            "power": row["power"], "accuracy": row["accuracy"], "pp": row["pp"],
            "description": row["description"]}

    # Populate ability names for species
    for sid in _species:
        sp = _species[sid]
        sp["abilityNames"] = [_abilities[aid]["name"] for aid in sp["abilities"] if aid in _abilities]
        hid = sp.get("hiddenAbilityID", 0)
        sp["hiddenAbilityName"] = _abilities[hid]["name"] if hid and hid in _abilities else ""

    # Abilities
    for row in conn.execute("SELECT * FROM abilities"):
        _abilities[row["id"]] = {"id": row["id"], "name": row["name"]}

    # Items
    for row in conn.execute("SELECT * FROM items"):
        _items[row["id"]] = {"id": row["id"], "name": row["name"],
            "description": row["description"]}

    conn.close()

load_all_data()

def fuzzy_match(query: str, name: str) -> bool:
    """Characters-in-order fuzzy match. 'pik' matches 'Pikachu', 'chr' matches 'Charizard'."""
    q = query.lower(); n = name.lower(); qi = 0
    for c in n:
        if qi < len(q) and c == q[qi]: qi += 1
    return qi == len(q)

ENUMS = {"type": [
    {"value":0,"name":"Normal","label":"一般"},{"value":1,"name":"Fire","label":"火"},
    {"value":2,"name":"Water","label":"水"},{"value":3,"name":"Electric","label":"电"},
    {"value":4,"name":"Grass","label":"草"},{"value":5,"name":"Ice","label":"冰"},
    {"value":6,"name":"Fighting","label":"格斗"},{"value":7,"name":"Poison","label":"毒"},
    {"value":8,"name":"Ground","label":"地面"},{"value":9,"name":"Flying","label":"飞行"},
    {"value":10,"name":"Psychic","label":"超能力"},{"value":11,"name":"Bug","label":"虫"},
    {"value":12,"name":"Rock","label":"岩石"},{"value":13,"name":"Ghost","label":"幽灵"},
    {"value":14,"name":"Dragon","label":"龙"},{"value":15,"name":"Dark","label":"恶"},
    {"value":16,"name":"Steel","label":"钢"},{"value":17,"name":"Fairy","label":"妖精"}],
    "category": [{"value":0,"name":"Physical","label":"物理"},{"value":1,"name":"Special","label":"特殊"},{"value":2,"name":"Status","label":"变化"}],
    "weather": [{"value":0,"name":"Clear","label":"无天气"},{"value":1,"name":"Rain","label":"雨天"},{"value":2,"name":"Sun","label":"晴天"},{"value":3,"name":"Sandstorm","label":"沙暴"},{"value":4,"name":"Hail","label":"冰雹"},{"value":5,"name":"Snow","label":"雪天"}],
    "status": [{"value":0,"name":"None","label":"无"},{"value":1,"name":"Burn","label":"灼伤"},{"value":2,"name":"Freeze","label":"冰冻"},{"value":3,"name":"Paralysis","label":"麻痹"},{"value":4,"name":"Poison","label":"中毒"},{"value":5,"name":"Sleep","label":"睡眠"},{"value":7,"name":"ToxicPoison","label":"剧毒"},{"value":8,"name":"Confusion","label":"混乱"}],
}

# ============================================================
# Battle Daemon — long-running engine subprocess per battle
# ============================================================
import time, threading

class BattleEngine:
    """Wraps C++ --daemon mode. Files pre-written, filesystem polling only."""

    def __init__(self, battle_id, init_json):
        self.battle_id = battle_id
        self.init_json = init_json
        self.turn = 0
        self.ended = False
        self.work_dir = Path(tempfile.mkdtemp(prefix=f"battle_{battle_id}_"))
        self.turns = {}
        self._lock = threading.Lock()
        self._proc = None

        # Setup (must create output dir too — createDeferred doesn't)
        (self.work_dir / "cache" / "input").mkdir(parents=True)
        (self.work_dir / "cache" / "output").mkdir(parents=True)
        data_link = self.work_dir / "data"
        if not data_link.exists():
            os.symlink(str(DATA_DIR), str(data_link))

        # Write init + turn 0 BEFORE starting daemon
        side_a = init_json.get("side_a", {})
        side_b = init_json.get("side_b", {})
        with open(self.work_dir / "cache/input/side_a.json", "w") as f: json.dump(side_a, f)
        with open(self.work_dir / "cache/input/side_b.json", "w") as f: json.dump(side_b, f)
        with open(self.work_dir / "cache/input/1_input_0.json", "w") as f: json.dump({"type": "pass"}, f)
        with open(self.work_dir / "cache/input/2_input_0.json", "w") as f: json.dump({"type": "pass"}, f)

        # Start daemon (stdout/stderr to DEVNULL, poll filesystem only)
        self._proc = subprocess.Popen(
            [str(ENGINE_BIN), "--daemon"],
            cwd=str(self.work_dir),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        logger.info(f"[Engine:{battle_id}] Daemon started, waiting for turn 0...")
        self._wait_output(0, timeout=30)
        logger.info(f"[Engine:{battle_id}] Turn 0 ready")

    def _wait_output(self, turn_num, timeout=30):
        """Poll for output_N.json on filesystem."""
        f = self.work_dir / "cache" / "output" / f"output_{turn_num}.json"
        dl = time.time() + timeout
        while time.time() < dl:
            if f.exists():
                time.sleep(0.05)
                with open(f) as fh: return enrich_events(json.load(fh))
            if self._proc and self._proc.poll() is not None:
                raise RuntimeError(f"Engine exited (code {self._proc.returncode})")
            time.sleep(0.1)
        raise TimeoutError(f"Timeout waiting output_{turn_num}")

    def get_state(self):
        f = self.work_dir / "cache" / "output" / f"output_{self.turn}.json"
        if f.exists():
            with open(f) as fh: return enrich_events(json.load(fh))
        return {"turn": 0, "battle": {"sides": [
            {"name": self.init_json.get("side_a",{}).get("name","A"), "pokemons": [], "active": 0},
            {"name": self.init_json.get("side_b",{}).get("name","B"), "pokemons": [], "active": 0}]}}

    def process_force_switch(self, side, switch_index):
        """Process a forced switch after KO. Returns updated state or None."""
        with self._lock:
            prefix = "1" if side in ("a", "A") else "2"
            tfile = self.work_dir / f"cache/input/{prefix}_input_{self.turn+1}.json"
            with open(tfile, "w") as f:
                json.dump({"type": "switch", "switch_index": switch_index}, f)
            return self._run()

    def process_turn(self, actions):
        with self._lock:
            if self.ended: return None
            nt = len(self.turns) + 1
            self.turns[nt] = actions
            for act in actions:
                clean = {k: v for k, v in act.items() if v is not None}
                side = clean.pop("side", "").lower()
                pfx = "1" if side in ("a", "side_a", "player_a") else "2"
                with open(self.work_dir / f"cache/input/{pfx}_input_{nt}.json", "w") as f: json.dump(clean, f)
            result = self._wait_output(nt, timeout=30)
            self.turn = nt
            for sd in result.get("battle", result).get("sides", []):
                if sd.get("pokemons") and all(p.get("fainted") for p in sd["pokemons"]):
                    self.ended = True; break
            return result

    def cleanup(self):
        try:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate(); self._proc.wait(timeout=3)
        except: pass
        shutil.rmtree(self.work_dir, ignore_errors=True)
# ============================================================

WEATHER_NAMES = {0:"无天气",1:"雨天☔",2:"晴天☀️",3:"沙暴🏜️",4:"冰雹🌨️",5:"雪天❄️"}
FIELD_NAMES = {0:"无场地",1:"精神场地🔮",2:"电气场地⚡",3:"青草场地🌿",4:"薄雾场地🌫️",5:"戏法空间🔄"}

def enrich_events(data):
    battle = data.get("battle", data)
    # Add species names + detect pendingSwitch
    pending_sides = []
    for sd in battle.get("sides", []):
        if sd.get("_pendingSwitch"):
            pending_sides.append(sd.get("name", "?"))
        for p in sd.get("pokemons", []):
            sid = p.get("speciesId", 0)
            if sid and sid in _species:
                p["_speciesName"] = _species[sid]["name"]
    data["_hasPendingSwitch"] = len(pending_sides) > 0

    # Add weather/field info to every event's context
    w = battle.get("weather", {})
    f = battle.get("field", {})
    wt = w.get("type", 0) if isinstance(w, dict) else 0
    ft = f.get("type", 0) if isinstance(f, dict) else 0
    wt_dur = w.get("duration", 0) if isinstance(w, dict) else 0
    ft_dur = f.get("duration", 0) if isinstance(f, dict) else 0

    data["_weather"] = {"type": wt, "label": WEATHER_NAMES.get(wt,""), "duration": wt_dur}
    data["_field"] = {"type": ft, "label": FIELD_NAMES.get(ft,""), "duration": ft_dur}

    for ev in data.get("events", []):
        if not ev.get("event_type"):
            d = ev.get("description", "")
            if "上场" in d: ev["event_type"] = "switch_in"
            elif "特性" in d: ev["event_type"] = "ability_trigger"
            elif "道具" in d and "阻止" in d: ev["event_type"] = "item_blocked"
            elif "道具" in d: ev["event_type"] = "item_trigger"
            elif any(w in d.lower() for w in ["paralysis","paralyz","burn","灼伤","麻痹","中毒","poison","睡眠","sleep","冰冻","freeze","混乱"]):
                ev["event_type"] = "status_apply"
            elif "回复" in d: ev["event_type"] = "heal"
            elif "伤害" in d: ev["event_type"] = "damage"
            elif "能力" in d and ("上升" in d or "下降" in d): ev["event_type"] = "stat_change"
            elif "濒死" in d or "倒下" in d: ev["event_type"] = "faint"
            elif "天气" in d: ev["event_type"] = "weather"
            else: ev["event_type"] = "info"
    return data

# ============================================================
# In-memory state
# ============================================================
battles_db: dict = {}     # battle_id → battle metadata
battle_engines: dict = {} # battle_id → BattleEngine instance
match_pool: list = []
match_battles: dict = {}  # player_id → {battle_id, side}
match_pending: dict = {}  # battle_id → {side: action}
connections: dict[str, WebSocket] = {}
ws_clients: set[WebSocket] = set()


# ============================================================
# WebSocket Endpoint
# ============================================================
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    player_id = None
    logger.info(f"WebSocket connected (live clients: {len(ws_clients)})")

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")
            data = msg.get("data", {})
            req_id = msg.get("id", None)  # optional request tracking

            try:
                if msg_type == "handshake":
                    player_id = data.get("player_id", str(uuid.uuid4())[:8])
                    connections[player_id] = ws
                    await send(ws, "handshake_ok", {"player_id": player_id})

                # --- Battles ---
                elif msg_type == "create_battle":
                    bid = str(uuid.uuid4())[:8]
                    team_a = json.loads(data["team_a_json"])
                    team_b = json.loads(data["team_b_json"])
                    seed = data.get("seed", 0)
                    init_json = {"side_a": team_a, "side_b": team_b, "seed": seed}
                    loop = asyncio.get_running_loop()
                    daemon = await loop.run_in_executor(None, lambda: BattleEngine(bid, init_json))
                    battle_engines[bid] = daemon
                    state = daemon.get_state()
                    battle = {"id": bid, "status": "active", "total_turns": 0,
                              "init_json": json.dumps(init_json), "current_state": state}
                    battles_db[bid] = battle
                    await send(ws, "battle_created", {"battle": battle, "state": state})

                elif msg_type == "process_turn":
                    battle_id = data["battle_id"]
                    daemon = battle_engines.get(battle_id)
                    battle = battles_db.get(battle_id)
                    if not daemon or not battle:
                        await send(ws, "error", {"message": "Battle not found"}, req_id); continue
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, lambda: daemon.process_turn(data["actions"]))
                    if result is None:
                        await send(ws, "error", {"message": "Turn processing failed"}, req_id); continue
                    battle["total_turns"] = daemon.turn
                    battle["current_state"] = result
                    if daemon.ended:
                        battle["status"] = "completed"
                        daemon.cleanup()
                    await send(ws, "turn_processed", {"battle_id": battle_id, "turn": daemon.turn,
                                "status": battle["status"], "state": result})

                elif msg_type == "get_battle":
                    b = battles_db.get(data["battle_id"])
                    await send(ws, "battle_data", b or {})

                elif msg_type == "get_battles":
                    blist = list(battles_db.values())
                    blist.sort(key=lambda x: str(x.get("id","")), reverse=True)
                    await send(ws, "battles_list", blist[:50])

                # --- Matchmaking ---
                elif msg_type == "join_matchmaking":
                    pid = data["player_id"]
                    team_json = data["team_json"]
                    global match_pool
                    # Check if already in pool
                    already = any(p["player_id"] == pid for p in match_pool)
                    if already:
                        await send(ws, "matchmaking_status", {"status": "already_queued", "pool_size": len(match_pool)})
                        continue
                    match_pool.append({"player_id": pid, "team_json": team_json})
                    await send(ws, "matchmaking_status", {"status": "waiting", "pool_size": len(match_pool)})

                    if len(match_pool) >= 2:
                        p1 = match_pool.pop(0)
                        # Find a DIFFERENT player to match with (skip self-matches from duplicate tabs)
                        p2 = None
                        for i, p in enumerate(match_pool):
                            if p["player_id"] != p1["player_id"]:
                                p2 = match_pool.pop(i)
                                break
                        if p2 is None:
                            # Only same user in pool, put p1 back
                            match_pool.insert(0, p1)
                            continue
                        bid = str(uuid.uuid4())[:8]
                        team_a, team_b = json.loads(p1["team_json"]), json.loads(p2["team_json"])
                        init_json = {"side_a": team_a, "side_b": team_b, "seed": 42}
                        logger.info(f"Match! {p1['player_id']} vs {p2['player_id']} → {bid}, starting engine...")
                        # Run daemon init in thread pool to not block event loop
                        loop = asyncio.get_running_loop()
                        daemon = await loop.run_in_executor(None, lambda: BattleEngine(bid, init_json))
                        battle_engines[bid] = daemon
                        state = daemon.get_state()
                        logger.info(f"Match engine ready for {bid}")
                        battle = {"id": bid, "player_a_id": p1["player_id"], "player_b_id": p2["player_id"],
                                  "seed": 42, "status": "active", "total_turns": 0,
                                  "init_json": json.dumps(init_json), "current_state": state}
                        battles_db[bid] = battle
                        match_battles[p1["player_id"]] = {"battle_id": bid, "side": "a"}
                        match_battles[p2["player_id"]] = {"battle_id": bid, "side": "b"}
                        w1, w2 = connections.get(p1["player_id"]), connections.get(p2["player_id"])
                        logger.info(f"Sending matched: p1={p1['player_id']} ws={'OK' if w1 else 'MISSING'}, p2={p2['player_id']} ws={'OK' if w2 else 'MISSING'}")
                        if w1: await send(w1, "matched", {"battle_id": bid, "side": "a", "state": state})
                        if w2: await send(w2, "matched", {"battle_id": bid, "side": "b", "state": state})
                        logger.info(f"Matched messages sent for {bid}")

                elif msg_type == "force_switch":
                    battle_id = data["battle_id"]
                    daemon = battle_engines.get(battle_id)
                    if not daemon:
                        await send(ws, "error", {"message": "Battle not found"}, req_id); continue
                    side = data.get("side", "a")
                    switch_index = data.get("switch_index", 0)
                    # Process forced switch via engine
                    loop = asyncio.get_running_loop()
                    state = await loop.run_in_executor(None, lambda: daemon.process_force_switch(side, switch_index))
                    battle = battles_db.get(battle_id)
                    if battle:
                        battle["current_state"] = state or battle.get("current_state")
                    # Push to both players
                    for pid_s, info in match_battles.items():
                        if info.get("battle_id") == battle_id:
                            w = connections.get(pid_s)
                            if w: await send(w, "turn_processed", {"battle_id": battle_id,
                                "turn": daemon.turn, "status": battle["status"] if battle else "active", "state": state or battle["current_state"]})
                    await send(ws, "force_switch_done", {"state": state}, req_id)

                elif msg_type == "submit_action":
                    battle_id = data["battle_id"]
                    battle = battles_db.get(battle_id)
                    daemon = battle_engines.get(battle_id)
                    if not battle or not daemon:
                        await send(ws, "error", {"message": "Battle not found"}, req_id); continue
                    action = data["action"]
                    side = action.get("side", "")
                    clean = {k: v for k, v in action.items() if v is not None and k != "side"}
                    pending = match_pending.setdefault(battle_id, {})
                    pending[side] = clean

                    if len(pending) >= 2:
                        actions_list = [{"side": s, **pending[s]} for s in ["a","b"] if s in pending]
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(None, lambda: daemon.process_turn(actions_list))
                        match_pending.pop(battle_id, None)
                        battle["total_turns"] = daemon.turn
                        battle["current_state"] = result or battle.get("current_state")
                        if daemon.ended:
                            battle["status"] = "completed"
                            daemon.cleanup()
                        # Push to both players
                        for pid_s, info in match_battles.items():
                            if info.get("battle_id") == battle_id:
                                w = connections.get(pid_s)
                                if w: await send(w, "turn_processed", {"battle_id": battle_id,
                                    "turn": daemon.turn, "status": battle["status"], "state": result or battle["current_state"]})
                    else:
                        await send(ws, "action_submitted", {"side": side})

                # --- Data ---
                elif msg_type == "get_species":
                    q = data.get("search", "").strip()
                    limit = int(data.get("limit", 15))
                    if q:
                        results = [s for s in _species.values() if fuzzy_match(q, s["name"])][:limit]
                    else:
                        results = list(_species.values())[:limit]
                    await send(ws, "species_list", results, req_id)

                elif msg_type == "get_moves":
                    q = data.get("search", "").strip()
                    limit = data.get("limit", 15)
                    learnset = data.get("learnset", [])  # optional: list of allowed move IDs
                    # Build candidate pool (full or learnset-filtered)
                    if learnset:
                        pool = [_moves[i] for i in learnset if i in _moves]
                    else:
                        pool = list(_moves.values())
                    if q:
                        results = [m for m in pool if fuzzy_match(q, m["name"])][:limit]
                    else:
                        results = pool[:limit]
                    await send(ws, "moves_list", results, req_id)

                elif msg_type == "get_move":
                    mv = _moves.get(data["id"])
                    await send(ws, "move_data", mv or {}, req_id)

                elif msg_type == "get_ability":
                    ab = _abilities.get(data["id"])
                    await send(ws, "ability_data", ab or {}, req_id)

                elif msg_type == "get_abilities":
                    q = data.get("search", "").strip()
                    if q:
                        results = [a for a in _abilities.values() if fuzzy_match(q, a["name"])][:15]
                    else:
                        common = [9,66,3,26,168,45,146,67,10]
                        results = [_abilities[i] for i in common if i in _abilities]
                    await send(ws, "abilities_list", results, req_id)

                elif msg_type == "get_items":
                    q = data.get("search", "").strip()
                    limit = int(data.get("limit", 200))
                    # Filter battle-relevant items: skip pokeballs(-ball), potions, TMs, etc.
                    skip_kw = ['-ball','potion','ether','elixir','revive','repel','tm','-mail',
                               'shard','stone','plate','incense','mulch','nugget','pearl','shoal',
                               'rare-candy','rare bone','big-mushroom','balm-mushroom',
                               'tiny-mushroom','stardust','star-piece','comet-shard',
                               'rm-','pp-up','pp-max','heart-scale','honey',
                               'growth-','stable-','gooey-','damp-','heat-','smooth-','icy-']
                    def is_battle_item(it):
                        name = it.get('name','').lower()
                        for kw in skip_kw:
                            if kw in name: return False
                        return True
                    battle_items = [i for i in _items.values() if is_battle_item(i)]
                    if q:
                        results = [i for i in battle_items if fuzzy_match(q, i["name"])][:limit]
                    else:
                        results = battle_items[:limit]
                    await send(ws, "items_list", results, req_id)

                elif msg_type == "get_sprite_url":
                    sid = data.get("id", 0)
                    sp = _species.get(sid, {})
                    name = sp.get("name", "").lower().replace(" ", "").replace(".", "").replace("'", "").replace("-", "")
                    # Pokemon Showdown CDN (fast, optimized for sprites)
                    url = f"https://play.pokemonshowdown.com/sprites/ani/{name}.gif" if name else ""
                    await send(ws, "sprite_url", {"id": sid, "url": url}, req_id)

                elif msg_type == "get_enums":
                    await send(ws, "enums", ENUMS, req_id)

                elif msg_type == "get_global_stats":
                    import sqlite3
                    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
                    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    total_teams = conn.execute("SELECT COUNT(*) FROM user_teams").fetchone()[0]
                    conn.close()
                    await send(ws, "global_stats", {
                        "total_battles": len(battles_db),
                        "completed": sum(1 for b in battles_db.values() if b.get("status")=="completed"),
                        "match_pool": len(match_pool),
                        "total_players": total_users,
                        "total_teams": total_teams,
                    }, req_id)

                elif msg_type == "get_deep_stats":
                    """Return the full deep analysis package."""
                    pkg = get_deep_stats_package()
                    await send(ws, "deep_stats", pkg["data"], req_id)

                elif msg_type == "get_type_distribution":
                    types = get_type_distribution()
                    await send(ws, "type_distribution", types, req_id)

                # --- Users & Teams (SQLite-backed) ---
                elif msg_type == "save_user":
                    import sqlite3
                    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
                    name = data.get("name", "Trainer")
                    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (name,))
                    conn.commit(); conn.close()
                    await send(ws, "user_saved", {"username": name}, req_id)

                elif msg_type == "save_team":
                    import sqlite3
                    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
                    username = data.get("user_id", data.get("username", ""))
                    team_name = data.get("name", "Team")
                    team_json = json.dumps(data.get("pokemon", []))
                    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
                    conn.execute("INSERT OR REPLACE INTO user_teams (username,team_name,team_json,updated_at) VALUES (?,?,?,datetime('now'))",
                                 (username, team_name, team_json))
                    conn.commit(); conn.close()
                    await send(ws, "team_saved", {"team_name": team_name}, req_id)

                elif msg_type == "delete_team":
                    import sqlite3
                    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
                    username = data.get("username", "")
                    team_name = data.get("team_name", "")
                    conn.execute("DELETE FROM user_teams WHERE username=? AND team_name=?", (username, team_name))
                    conn.commit(); conn.close()
                    await send(ws, "team_deleted", {"team_name": team_name}, req_id)

                elif msg_type == "get_user_teams":
                    import sqlite3
                    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
                    username = data.get("user_id", data.get("username", ""))
                    rows = conn.execute("SELECT * FROM user_teams WHERE username=? ORDER BY updated_at DESC", (username,)).fetchall()
                    conn.close()
                    teams = [{"name": r[1], "pokemon": json.loads(r[2])} for r in rows]
                    await send(ws, "user_teams", teams, req_id)

                # --- Health ---
                elif msg_type == "ping":
                    await send(ws, "pong", {"engine": ENGINE_BIN.exists(), "species": len(_species)})

                else:
                    await send(ws, "error", {"message": f"Unknown type: {msg_type}"}, req_id)

            except Exception as e:
                logger.error(f"Handler error: {e}", exc_info=True)
                await send(ws, "error", {"message": str(e)}, req_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {player_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(ws)
        if player_id:
            # Remove from match pool and battles (uses global lists from handlers)
            for pl in [match_pool]: pl[:] = [p for p in pl if p["player_id"] != player_id]
            match_battles.pop(player_id, None)
            # Remove from connections
            if player_id in connections:
                del connections[player_id]


async def send(ws: WebSocket, msg_type: str, data, req_id: str = None):
    msg = {"type": msg_type, "data": data}
    if req_id: msg["id"] = req_id
    await ws.send_json(msg)


async def broadcast(msg_type: str, data):
    """Send a message to all connected WebSocket clients."""
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json({"type": msg_type, "data": data})
        except Exception:
            dead.add(ws)
    ws_clients.difference_update(dead)


# ── Background file watcher for live stats streaming ──────────
_live_watcher_task = None
_last_battle_mtime = 0.0
_spark_running = False
WATCH_INTERVAL = 15  # seconds


def _get_latest_battle_mtime(battle_dir: Path) -> float:
    """Get the max mtime of all output JSON files under battle_dir."""
    max_mtime = 0.0
    try:
        for f in battle_dir.rglob("output_*.json"):
            try:
                mtime = f.stat().st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
            except OSError:
                pass
    except Exception:
        pass
    return max_mtime


async def _run_import_and_broadcast():
    """Import new battle data into SQLite, then broadcast to clients."""
    global _last_battle_mtime, _spark_running
    if _spark_running:
        return
    _spark_running = True
    try:
        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(None, _import_battles)
        battle_dir = PROJECT_ROOT / "battle_logs"
        _last_battle_mtime = _get_latest_battle_mtime(battle_dir)
        if count > 0:
            from sql_analytics import invalidate
            invalidate()
            # Lightweight broadcast — just rankings, no HP traces
            await broadcast("stats_updated", {
                "species_usage": get_meta_species(),
                "move_usage": get_meta_moves(),
                "item_usage": get_meta_items(),
                "ability_usage": get_meta_abilities(),
                "type_distribution": get_type_distribution(),
                "survival": get_battle_survival(),
                "summary": get_analysis_summary().get("data", {}),
            })
            logger.info(f"[live] Imported {count} rows, broadcasted stats_updated")
    except Exception as e:
        logger.error(f"[live] Import/broadcast error: {e}")
    finally:
        _spark_running = False


def _import_battles() -> int:
    """Import new battles from JSON files into SQLite. Returns row count."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "api-server"))
    from battle_importer import import_new_battles
    return import_new_battles()


async def _live_watcher_loop():
    """Poll battle_logs for new output files, trigger Spark on changes."""
    global _last_battle_mtime
    logger.info("[live] File watcher started")
    while True:
        await asyncio.sleep(WATCH_INTERVAL)
        try:
            battle_dir = PROJECT_ROOT / "battle_logs"
            if not battle_dir.is_dir():
                continue
            latest = _get_latest_battle_mtime(battle_dir)
            if latest > _last_battle_mtime:
                _last_battle_mtime = latest
                logger.info("[live] New battle data detected, importing...")
                await _run_import_and_broadcast()
        except Exception as e:
            logger.error(f"[live] Watcher error: {e}")


from config import ENABLE_WATCHER

if ENABLE_WATCHER:
    @app.on_event("startup")
    async def start_live_watcher():
        global _live_watcher_task, _last_battle_mtime
        battle_dir = PROJECT_ROOT / "battle_logs"
        _last_battle_mtime = _get_latest_battle_mtime(battle_dir)
        _live_watcher_task = asyncio.create_task(_live_watcher_loop())
        logger.info("[live] Live watcher started")

    @app.on_event("shutdown")
    async def stop_live_watcher():
        global _live_watcher_task
        if _live_watcher_task:
            _live_watcher_task.cancel()
            _live_watcher_task = None
            logger.info("[live] Live watcher stopped")


@app.get("/api/v1/scout")
def api_scout(username: str = Query("", description="Username to scout")):
    """Scout an opponent: analyze their teams, preferred Pokemon, moves, and style."""
    import sqlite3
    if not username.strip():
        return {"ok": False, "error": "Missing username parameter"}

    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
    conn.row_factory = sqlite3.Row

    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        conn.close()
        return {"ok": False, "error": f"User '{username}' not found"}

    teams_raw = conn.execute(
        "SELECT * FROM user_teams WHERE username=? ORDER BY updated_at DESC",
        (username,)
    ).fetchall()
    conn.close()

    teams = []
    type_counts = {}
    move_counts = {}
    species_counts = {}
    all_pokemon = []

    for t in teams_raw:
        pokemon_list = json.loads(t["team_json"]) if isinstance(t["team_json"], str) else t["team_json"]
        resolved = []
        for p in pokemon_list:
            sid = p.get("speciesID", 0)
            sp = _species.get(sid, {})
            sp_name = sp.get("name", f"#{sid}")
            sp_types = sp.get("types", [])

            moves_resolved = []
            for mid in p.get("moves", []):
                mv = _moves.get(mid, {})
                mv_name = mv.get("name", f"#{mid}")
                mv_type = mv.get("type", 0)
                moves_resolved.append({"id": mid, "name": mv_name, "type": mv_type})
                move_counts[mv_name] = move_counts.get(mv_name, 0) + 1

            ability_id = p.get("ability", 0)
            ab = _abilities.get(ability_id, {})
            ability_name = ab.get("name", f"#{ability_id}")

            item_id = p.get("item", 0)
            it = _items.get(item_id, {})
            item_name = it.get("name", f"#{item_id}") if item_id else ""

            nature_names = {
                0:"Hardy",1:"Lonely",2:"Brave",3:"Adamant",4:"Naughty",
                5:"Bold",6:"Docile",7:"Relaxed",8:"Impish",9:"Lax",
                10:"Timid",11:"Hasty",12:"Serious",13:"Jolly",14:"Naive",
                15:"Modest",16:"Mild",17:"Quiet",18:"Bashful",19:"Rash",
                20:"Calm",21:"Gentle",22:"Sassy",23:"Careful",24:"Quirky"
            }
            nature_name = nature_names.get(p.get("nature", 0), "?")

            for t_name in sp_types:
                if t_name:
                    type_counts[t_name] = type_counts.get(t_name, 0) + 1

            species_counts[sp_name] = species_counts.get(sp_name, 0) + 1

            resolved.append({
                "species_id": sid,
                "species_name": sp_name,
                "sprite_url": f"/sprites/{sid}.gif",
                "types": sp_types,
                "moves": moves_resolved,
                "ability": {"id": ability_id, "name": ability_name},
                "item": {"id": item_id, "name": item_name},
                "nature": {"id": p.get("nature", 0), "name": nature_name},
            })

        teams.append({"name": t["team_name"], "pokemon": resolved, "updated_at": t["updated_at"]})
        all_pokemon.extend(resolved)

    # Style analysis
    top_types = sorted(type_counts.items(), key=lambda x: -x[1])[:5]
    top_moves = sorted(move_counts.items(), key=lambda x: -x[1])[:5]
    top_species = sorted(species_counts.items(), key=lambda x: -x[1])[:5]

    style_tags = []
    if any(t[0] in ("fire","water","grass","electric") for t in top_types[:2]):
        style_tags.append("元素掌控者")
    if any(t[0] in ("dragon","steel","fairy") for t in top_types[:2]):
        style_tags.append("龙钢妖精使")
    if any(t[0] in ("ghost","dark","psychic") for t in top_types[:2]):
        style_tags.append("暗影灵能者")
    if sum(c for _,c in species_counts.items()) >= 5:
        style_tags.append("队伍构筑师")
    if len(teams) >= 2:
        style_tags.append("战术多变")
    if not style_tags:
        style_tags.append("新手训练家")

    return {
        "ok": True,
        "data": {
            "username": username,
            "created_at": user["created_at"],
            "style_tags": style_tags,
            "stats": {
                "total_teams": len(teams),
                "total_pokemon": len(all_pokemon),
                "unique_species": len(species_counts),
                "top_types": [{"name": n, "count": c} for n, c in top_types],
                "top_moves": [{"name": n, "count": c} for n, c in top_moves],
                "top_species": [{"name": n, "count": c} for n, c in top_species],
            },
            "teams": teams,
        }
    }

# ============================================================
# Health (REST fallback)
# ============================================================
@app.get("/api/v1/health")
def health():
    return {"ok": True, "data": {"mode": "websocket", "species": len(_species),
            "moves": len(_moves), "abilities": len(_abilities), "engine": ENGINE_BIN.exists()}}

@app.get("/api/v1/stats/global")
def api_global_stats_rest():
    """Global stats for frontend cards."""
    import sqlite3
    conn = sqlite3.connect(str(DATA_DIR / "pokemon.db"))
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_teams = conn.execute("SELECT COUNT(*) FROM user_teams").fetchone()[0]
    conn.close()
    return {
        "ok": True,
        "data": {
            "total_players": total_users,
            "total_battles": len(battles_db),
            "total_teams": total_teams,
            "total_completed_battles": sum(1 for b in battles_db.values() if b.get("status")=="completed"),
        }
    }

# ── Deep Analytics REST endpoints ─────────────────────────────
@app.get("/api/v1/stats/deep/summary")
def api_deep_summary():
    """Get analysis summary."""
    return get_analysis_summary()

@app.get("/api/v1/stats/deep/meta")
def api_deep_meta():
    """Get pokemon usage ranking."""
    return {"ok": True, "data": get_meta_species()}

@app.get("/api/v1/stats/deep/moves")
def api_deep_moves():
    """Get move usage ranking."""
    return {"ok": True, "data": get_meta_moves()}

@app.get("/api/v1/stats/deep/items")
def api_deep_items():
    """Get item usage ranking."""
    return {"ok": True, "data": get_meta_items()}

@app.get("/api/v1/stats/deep/abilities")
def api_deep_abilities():
    """Get ability usage ranking."""
    return {"ok": True, "data": get_meta_abilities()}

@app.get("/api/v1/stats/deep/types")
def api_deep_types():
    """Get type distribution."""
    return {"ok": True, "data": get_type_distribution()}

@app.get("/api/v1/stats/deep/battle")
def api_deep_battle():
    """Get battle HP curves."""
    return {"ok": True, "data": get_battle_hp_curve()}

@app.get("/api/v1/stats/deep/events")
def api_deep_events():
    """Get event type distribution."""
    return {"ok": True, "data": get_event_distribution()}

@app.get("/api/v1/stats/deep/survival")
def api_deep_survival():
    """Get pokemon survival rates."""
    return {"ok": True, "data": get_battle_survival()}

@app.get("/api/v1/stats/deep/team-synergy")
def api_team_synergy():
    return {"ok": True, "data": get_team_synergy()}

@app.get("/api/v1/stats/deep/head-to-head")
def api_head_to_head(s1: int = 0, s2: int = 0):
    return {"ok": True, "data": get_head_to_head(s1, s2)}

@app.get("/api/v1/stats/deep/live")
def api_deep_live():
    """Lightweight live endpoint — only ranking data, no HP traces."""
    return {"ok": True, "data": {
        "species_usage": get_meta_species(),
        "move_usage": get_meta_moves(),
        "item_usage": get_meta_items(),
        "ability_usage": get_meta_abilities(),
        "type_distribution": get_type_distribution(),
        "survival": get_battle_survival(),
        "summary": get_analysis_summary().get("data", {}),
    }}


@app.get("/api/v1/stats/deep/all")
def api_deep_all():
    """Get all deep stats in one call."""
    return get_deep_stats_package()

@app.get("/api/v1/stats/deep/pokemon/{species_id}")
def api_pokemon_detail(species_id: int):
    """Get per-species detail: ranked moves, items, abilities for a Pokemon."""
    data = get_species_detail(species_id)
    return {"ok": True, "data": data}


@app.get("/api/v1/stats/deep/pokemon-hp")
def api_pokemon_hp():
    """Get per-pokemon HP trace."""
    return {"ok": True, "data": get_pokemon_hp()}

@app.post("/api/v1/stats/deep/refresh")
def api_refresh_analysis():
    import subprocess
    script = Path(__file__).resolve().parent.parent / "scripts" / "run_analysis.sh"
    try:
        subprocess.run(["bash", str(script)], cwd=str(script.parent.parent), timeout=120)
    except: pass
    from analytics_service import get_deep_stats_package
    return get_deep_stats_package()

if __name__ == "__main__":
    logger.info(f"Engine: {ENGINE_BIN} — {'OK' if ENGINE_BIN.exists() else 'MISSING'}")
    logger.info(f"Data: {len(_species)} species, {len(_moves)} moves, {len(_abilities)} abilities")
    logger.info("Starting WebSocket server on ws://0.0.0.0:8000/ws ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
