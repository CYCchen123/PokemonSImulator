-- ============================================================
-- PokemonSimulator PostgreSQL 初始化
-- 自动执行于数据库首次创建时
-- ============================================================

-- 玩家表
CREATE TABLE IF NOT EXISTS players (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 队伍表
CREATE TABLE IF NOT EXISTS teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id   UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    name        VARCHAR(200) NOT NULL DEFAULT 'Untitled Team',
    pokemon_json JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_player ON teams(player_id);

-- 对战表
CREATE TABLE IF NOT EXISTS battles (
    id              UUID PRIMARY KEY,
    player_a_id     UUID REFERENCES players(id),
    player_b_id     UUID REFERENCES players(id),
    team_a_id       UUID REFERENCES teams(id),
    team_b_id       UUID REFERENCES teams(id),
    seed            INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    winner_side     VARCHAR(1),
    winner_player_id UUID REFERENCES players(id),
    total_turns     INTEGER DEFAULT 0,
    init_json       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_battles_status ON battles(status);
CREATE INDEX IF NOT EXISTS idx_battles_player_a ON battles(player_a_id);
CREATE INDEX IF NOT EXISTS idx_battles_player_b ON battles(player_b_id);
CREATE INDEX IF NOT EXISTS idx_battles_created ON battles(created_at DESC);

-- 对战回合记录表
CREATE TABLE IF NOT EXISTS battle_turns (
    id          SERIAL PRIMARY KEY,
    battle_id   UUID NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    hdfs_path   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(battle_id, turn_number)
);

CREATE INDEX IF NOT EXISTS idx_battle_turns_battle ON battle_turns(battle_id);

-- 宝可梦使用率统计表 (PySpark 批量写入)
CREATE TABLE IF NOT EXISTS pokemon_usage_stats (
    id              SERIAL PRIMARY KEY,
    species_id      INTEGER NOT NULL,
    species_name    VARCHAR(100),
    times_used      INTEGER DEFAULT 0,
    times_koed      INTEGER DEFAULT 0,
    avg_hp_percent  NUMERIC(5,2),
    total_appearances INTEGER DEFAULT 0,
    period_start    DATE,
    period_end      DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_stats_species ON pokemon_usage_stats(species_id);
CREATE INDEX IF NOT EXISTS idx_usage_stats_period ON pokemon_usage_stats(period_start, period_end);

-- 对战分析聚合表 (Spark Streaming 写入)
CREATE TABLE IF NOT EXISTS battle_analytics (
    id              SERIAL PRIMARY KEY,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    event_type      VARCHAR(50),
    count           INTEGER DEFAULT 0,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_window ON battle_analytics(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON battle_analytics(event_type);

-- 更新队伍 updated_at 触发器
CREATE OR REPLACE FUNCTION update_team_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_team_updated ON teams;
CREATE TRIGGER trg_team_updated
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_team_timestamp();
