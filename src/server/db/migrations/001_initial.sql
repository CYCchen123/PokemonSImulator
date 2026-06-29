-- PokemonSimulator Database Schema v1
-- Migration 001: Initial schema

-- ==========================================
-- Static reference data (mirrors data/*.json)
-- ==========================================

CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type1 TEXT NOT NULL,
    type2 TEXT DEFAULT '',
    base_hp INTEGER NOT NULL,
    base_atk INTEGER NOT NULL,
    base_def INTEGER NOT NULL,
    base_spa INTEGER NOT NULL,
    base_spd INTEGER NOT NULL,
    base_spe INTEGER NOT NULL,
    ability_ids TEXT DEFAULT '[]',
    hidden_ability_id INTEGER DEFAULT 0,
    egg_groups TEXT DEFAULT '[]',
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    power INTEGER DEFAULT 0,
    accuracy INTEGER DEFAULT 100,
    pp INTEGER NOT NULL DEFAULT 0,
    priority INTEGER DEFAULT 0,
    target TEXT DEFAULT 'opponent',
    effect TEXT DEFAULT '',
    effect_chance INTEGER DEFAULT 0,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_battle INTEGER DEFAULT 1,
    data_json TEXT NOT NULL
);

-- ==========================================
-- Player management
-- ==========================================

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ==========================================
-- Team management
-- ==========================================

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    team_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_teams_player ON teams(player_id);

-- ==========================================
-- Battles
-- ==========================================

CREATE TABLE IF NOT EXISTS battles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_a_id INTEGER REFERENCES players(id),
    player_b_id INTEGER REFERENCES players(id),
    team_a_id INTEGER REFERENCES teams(id),
    team_b_id INTEGER REFERENCES teams(id),
    seed INTEGER NOT NULL DEFAULT 0,
    winner_side TEXT DEFAULT '',
    winner_player_id INTEGER REFERENCES players(id),
    total_turns INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    init_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_battles_player_a ON battles(player_a_id);
CREATE INDEX IF NOT EXISTS idx_battles_player_b ON battles(player_b_id);
CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status);

-- ==========================================
-- Battle turns (per-turn snapshots)
-- ==========================================

CREATE TABLE IF NOT EXISTS battle_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL REFERENCES battles(id),
    turn_number INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    events_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(battle_id, turn_number)
);

CREATE INDEX IF NOT EXISTS idx_battle_turns_battle ON battle_turns(battle_id);

-- ==========================================
-- Battle events (indexed timeline)
-- ==========================================

CREATE TABLE IF NOT EXISTS battle_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL REFERENCES battles(id),
    turn_number INTEGER NOT NULL,
    timeline_index INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    details_json TEXT NOT NULL,
    UNIQUE(battle_id, turn_number, timeline_index)
);

CREATE INDEX IF NOT EXISTS idx_battle_events_battle ON battle_events(battle_id);
CREATE INDEX IF NOT EXISTS idx_battle_events_type ON battle_events(event_type);

-- ==========================================
-- Player statistics (updated after each battle)
-- ==========================================

CREATE TABLE IF NOT EXISTS player_stats (
    player_id INTEGER PRIMARY KEY REFERENCES players(id),
    total_battles INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    total_turns_played INTEGER NOT NULL DEFAULT 0,
    avg_turns_per_battle REAL NOT NULL DEFAULT 0.0,
    win_rate REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ==========================================
-- Team statistics
-- ==========================================

CREATE TABLE IF NOT EXISTS team_stats (
    team_id INTEGER PRIMARY KEY REFERENCES teams(id),
    times_used INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    win_rate REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ==========================================
-- Move usage statistics
-- ==========================================

CREATE TABLE IF NOT EXISTS move_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    move_id INTEGER NOT NULL REFERENCES moves(id),
    battle_id INTEGER NOT NULL REFERENCES battles(id),
    times_used INTEGER NOT NULL DEFAULT 0,
    times_hit INTEGER NOT NULL DEFAULT 0,
    total_damage INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_move_stats_move ON move_stats(move_id);

-- ==========================================
-- Pokemon usage statistics
-- ==========================================

CREATE TABLE IF NOT EXISTS pokemon_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL REFERENCES species(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    times_used INTEGER NOT NULL DEFAULT 0,
    times_koed INTEGER NOT NULL DEFAULT 0,
    kos_scored INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pokemon_stats_species ON pokemon_stats(species_id);

-- ==========================================
-- Schema version tracking
-- ==========================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_version (version, description) VALUES (1, 'Initial schema');
