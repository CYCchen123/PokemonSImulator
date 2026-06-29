-- PokemonSimulator PostgreSQL Schema
-- Initialized on first container start

-- ============================================================
-- Players
-- ============================================================
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Teams
-- ============================================================
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL DEFAULT 'Untitled Team',
    pokemon_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_player ON teams(player_id);

-- ============================================================
-- Battles
-- ============================================================
CREATE TABLE IF NOT EXISTS battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_a_id UUID REFERENCES players(id),
    player_b_id UUID REFERENCES players(id),
    team_a_id UUID REFERENCES teams(id),
    team_b_id UUID REFERENCES teams(id),
    seed INTEGER NOT NULL DEFAULT 0,
    winner_side CHAR(1),
    winner_player_id UUID REFERENCES players(id),
    total_turns INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'completed', 'error')),
    init_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status);
CREATE INDEX IF NOT EXISTS idx_battles_player_a ON battles(player_a_id);
CREATE INDEX IF NOT EXISTS idx_battles_player_b ON battles(player_b_id);
CREATE INDEX IF NOT EXISTS idx_battles_created ON battles(created_at DESC);

-- ============================================================
-- Battle turns (metadata, raw JSON is in HDFS)
-- ============================================================
CREATE TABLE IF NOT EXISTS battle_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    battle_id UUID NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    hdfs_path VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(battle_id, turn_number)
);

CREATE INDEX IF NOT EXISTS idx_battle_turns_battle ON battle_turns(battle_id);

-- ============================================================
-- Statistics (written by Spark jobs)
-- ============================================================

-- Pokemon usage stats
CREATE TABLE IF NOT EXISTS pokemon_usage_stats (
    id SERIAL PRIMARY KEY,
    species_id INTEGER NOT NULL,
    species_name VARCHAR(100),
    times_used INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    avg_turns_alive DOUBLE PRECISION DEFAULT 0.0,
    times_koed INTEGER NOT NULL DEFAULT 0,
    kos_scored INTEGER NOT NULL DEFAULT 0,
    period VARCHAR(20) DEFAULT 'all_time',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pokemon_usage_species ON pokemon_usage_stats(species_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_usage_period ON pokemon_usage_stats(period);

-- Move usage stats
CREATE TABLE IF NOT EXISTS move_usage_stats (
    id SERIAL PRIMARY KEY,
    move_id INTEGER NOT NULL,
    move_name VARCHAR(100),
    times_used INTEGER NOT NULL DEFAULT 0,
    times_hit INTEGER NOT NULL DEFAULT 0,
    total_damage BIGINT NOT NULL DEFAULT 0,
    avg_damage DOUBLE PRECISION DEFAULT 0.0,
    accuracy_rate DOUBLE PRECISION DEFAULT 0.0,
    period VARCHAR(20) DEFAULT 'all_time',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_move_usage_move ON move_usage_stats(move_id);

-- Type matchup stats
CREATE TABLE IF NOT EXISTS type_matchup_stats (
    id SERIAL PRIMARY KEY,
    attacker_type VARCHAR(20) NOT NULL,
    defender_type1 VARCHAR(20) NOT NULL,
    defender_type2 VARCHAR(20) DEFAULT '',
    total_battles INTEGER NOT NULL DEFAULT 0,
    attacker_wins INTEGER NOT NULL DEFAULT 0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    period VARCHAR(20) DEFAULT 'all_time',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Player stats
CREATE TABLE IF NOT EXISTS player_stats (
    player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    total_battles INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    total_turns_played INTEGER NOT NULL DEFAULT 0,
    avg_turns_per_battle DOUBLE PRECISION DEFAULT 0.0,
    favorite_species_id INTEGER,
    most_used_move_id INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Global meta snapshot
-- ============================================================
CREATE TABLE IF NOT EXISTS meta_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_battles INTEGER NOT NULL DEFAULT 0,
    total_players INTEGER NOT NULL DEFAULT 0,
    top_species_ids JSONB DEFAULT '[]',
    top_move_ids JSONB DEFAULT '[]',
    top_team_archetypes JSONB DEFAULT '[]',
    report_json JSONB DEFAULT '{}',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(snapshot_date)
);

-- ============================================================
-- Insert some test data
-- ============================================================
INSERT INTO players (name) VALUES
    ('Player Alpha'),
    ('Player Beta')
ON CONFLICT (name) DO NOTHING;
