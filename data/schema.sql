-- PokemonSimulator Database Schema v2
-- Replaces data/*.json with SQLite for faster loading

-- ============================================================
-- Species (宝可梦种族)
-- ============================================================
CREATE TABLE IF NOT EXISTS species (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    type1           TEXT    NOT NULL,
    type2           TEXT    DEFAULT '',
    base_hp         INTEGER NOT NULL DEFAULT 0,
    base_atk        INTEGER NOT NULL DEFAULT 0,
    base_def        INTEGER NOT NULL DEFAULT 0,
    base_spa        INTEGER NOT NULL DEFAULT 0,
    base_spd        INTEGER NOT NULL DEFAULT 0,
    base_spe        INTEGER NOT NULL DEFAULT 0,
    height          INTEGER DEFAULT 0,
    weight          INTEGER DEFAULT 0,
    male_ratio      REAL    DEFAULT 0.5,
    evolution_level INTEGER DEFAULT 0,
    next_evolution  INTEGER DEFAULT 0,
    egg_group1      TEXT    DEFAULT '',
    egg_group2      TEXT    DEFAULT '',
    hidden_ability  INTEGER DEFAULT 0
);

-- ============================================================
-- Moves (技能)
-- ============================================================
CREATE TABLE IF NOT EXISTS moves (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    api_name        TEXT    DEFAULT '',
    type            TEXT    NOT NULL DEFAULT 'Normal',
    category        TEXT    NOT NULL DEFAULT 'Status',
    power           INTEGER DEFAULT 0,
    accuracy        INTEGER DEFAULT 100,
    pp              INTEGER DEFAULT 0,
    priority        INTEGER DEFAULT 0,
    target          TEXT    DEFAULT 'opponent',
    effect          TEXT    DEFAULT '',
    effect_chance   INTEGER DEFAULT 0,
    effect_param1   INTEGER DEFAULT 0,
    effect_param2   INTEGER DEFAULT 0,
    description     TEXT    DEFAULT ''
);

-- ============================================================
-- Abilities (特性)
-- ============================================================
CREATE TABLE IF NOT EXISTS abilities (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    api_name        TEXT    DEFAULT '',
    description     TEXT    DEFAULT ''
);

-- ============================================================
-- Items (道具)
-- ============================================================
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    api_name        TEXT    DEFAULT '',
    description     TEXT    DEFAULT '',
    is_battle       INTEGER DEFAULT 1
);

-- ============================================================
-- Species-Moves junction (种族可学技能)
-- ============================================================
CREATE TABLE IF NOT EXISTS learnsets (
    species_id  INTEGER NOT NULL REFERENCES species(id),
    move_id     INTEGER NOT NULL REFERENCES moves(id),
    PRIMARY KEY (species_id, move_id)
);
CREATE INDEX IF NOT EXISTS idx_learnset_species ON learnsets(species_id);
CREATE INDEX IF NOT EXISTS idx_learnset_move ON learnsets(move_id);

-- ============================================================
-- Species-Abilities junction (种族可用特性)
-- ============================================================
CREATE TABLE IF NOT EXISTS species_abilities (
    species_id  INTEGER NOT NULL REFERENCES species(id),
    ability_id  INTEGER NOT NULL REFERENCES abilities(id),
    is_hidden   INTEGER DEFAULT 0,
    PRIMARY KEY (species_id, ability_id)
);
CREATE INDEX IF NOT EXISTS idx_sa_species ON species_abilities(species_id);

-- ============================================================
-- Users & Teams (player data)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_teams (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    name        TEXT NOT NULL DEFAULT 'Untitled',
    team_json   TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_user_teams ON user_teams(user_id);
