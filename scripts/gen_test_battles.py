import json, random, os, shutil, subprocess

PROJECT = "/home/lenovo/PokemonSImulator"
CACHE_IN = os.path.join(PROJECT, "cache/input")
ENGINE = os.path.join(PROJECT, "build/PokemonSimulator")
BATTLE_OUT = os.path.join(PROJECT, "battle_logs")
os.makedirs(CACHE_IN, exist_ok=True)

SPECIES_POOLS = [
    [25, 26, 133, 134, 135, 136],
    [144, 145, 146, 150, 151, 249],
    [59, 130, 248, 373, 445, 448],
    [94, 197, 330, 445, 448, 658],
]
ABILITY_MAP = {25:9, 26:9, 133:50, 134:11, 135:10, 136:18,
               144:46, 145:46, 146:46, 150:46, 151:46, 249:46,
               59:22, 130:22, 248:45, 373:22, 445:8, 448:9,
               94:20, 197:20, 330:26, 658:92}
MOVES_POOLS = [
    [85, 97, 87, 24], [59, 58, 126, 14], [89, 90, 91, 92],
    [53, 59, 63, 115], [22, 75, 76, 79], [163, 37, 38, 53],
    [33, 34, 36, 38], [10, 52, 98, 33],
]

def make_pokemon(sid, moves):
    return {"ability": ABILITY_MAP.get(sid, 65),
            "evs": {"attack":0,"defense":0,"hp":0,"specialAttack":252,"specialDefense":0,"speed":252},
            "ivs": {"attack":31,"defense":31,"hp":31,"specialAttack":31,"specialDefense":31,"speed":31},
            "level": 50, "moves": moves, "nature": 0, "speciesID": sid,
            "item": random.choice([0,0,0,0,2,3,6])}

for bn in [3, 4, 5]:
    pool_a = SPECIES_POOLS[(bn-3) % len(SPECIES_POOLS)]
    pool_b = SPECIES_POOLS[(bn+1) % len(SPECIES_POOLS)]

    sa, sb = [], []
    for i in range(3):
        sa.append(make_pokemon(pool_a[i], MOVES_POOLS[(pool_a[i]+i)%len(MOVES_POOLS)][:4]))
        sb.append(make_pokemon(pool_b[i], MOVES_POOLS[(pool_b[i]+i+2)%len(MOVES_POOLS)][:4]))

    init = {"side_a": {"name": "Side A", "pokemon": sa},
            "side_b": {"name": "Side B", "pokemon": sb}}

    ids_a = [p["speciesID"] for p in sa]
    ids_b = [p["speciesID"] for p in sb]
    print(f"Battle {bn}: A={ids_a} vs B={ids_b}")

    # Clear and write init
    for old in os.listdir(CACHE_IN):
        if old.endswith(".json"):
            os.remove(os.path.join(CACHE_IN, old))
    with open(os.path.join(CACHE_IN, "init_request.json"), "w") as f:
        json.dump(init, f)

    # Generate matching turn actions for both sides (engine needs pairs)
    num_turns = random.randint(15, 25)
    for t in range(1, num_turns + 1):
        for side_num in [1, 2]:
            action = {"move_index": random.randint(0, 3),
                      "side": "a" if side_num == 1 else "b",
                      "type": "attack"}
            fname = f"{side_num}_input_{t}.json"
            with open(os.path.join(CACHE_IN, fname), "w") as f:
                json.dump(action, f)

    # Run engine
    result = subprocess.run([ENGINE, "--run-cache-input"], cwd=PROJECT,
                          capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  Engine error: {result.stderr[:200]}")

    # Copy output to battle_logs/<bn>/output/
    cache_out = os.path.join(PROJECT, "cache/output")
    out_dir = os.path.join(BATTLE_OUT, str(bn), "output")
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    for f in sorted(os.listdir(cache_out)):
        if f.startswith("output_"):
            shutil.copy(os.path.join(cache_out, f), os.path.join(out_dir, f))
            count += 1
    print(f"  -> {count} output files for {num_turns} turns")

print("Done!")
