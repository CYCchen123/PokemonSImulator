# PokemonSimulator - Resume Context

## Quick Start

```bash
# Build C++ engine
cmake -B build -S . -G Ninja && cmake --build build

# Start services
bash scripts/restart.sh

# Open http://localhost:5173
```

## Architecture

```
frontend/     Vue 3 SPA (Vite, Tailwind, Pinia, Vue Router)
api-server/   Python FastAPI + WebSocket gateway
src/          C++17 battle engine (daemon mode)
data/         pokemon.db (SQLite, 4MB, 6 tables)
```

## Key Paths

| Path | Purpose |
|------|---------|
| `api-server/standalone_server.py` | WebSocket server (port 8000) |
| `frontend/src/views/TeamBuilder.vue` | Team builder UI |
| `frontend/src/views/MatchmakingPage.vue` | Battle UI |
| `src/battle/Battle.cpp` | Core battle logic |
| `src/IO/GameDatabase.cpp` | SQLite data loader |
| `data/pokemon.db` | Game data (species/moves/abilities/items/learnsets) |

## Data Flow

```
Vue → WebSocket → Python gateway → C++ engine (--daemon subprocess)
                                      ↕ file-based IPC
                                   cache/input/  (turn actions)
                                   cache/output/ (battle state JSON)
```

## Database Tables

```sql
species (1025), moves (937), abilities (367), items (2175)
learnsets (78512), species_abilities (2411)
users, user_teams
```

## Spritesheet

```bash
python3 scripts/build_icon_sheet.py  # Rebuild from local GIFs
```

## Important Notes

- Engine uses `--daemon` mode (persistent subprocess, maintains battle state)
- Species data loaded via SQLite (not JSON) — was the fix for daemon hang
- `enrich_events()` injects `_speciesName` into battle state
- `typeColor()` helper is case-insensitive (DB has lowercase types)
- Match pool auto-cleans disconnected players
