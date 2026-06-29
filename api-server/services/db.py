"""
Database connection and operations for PokemonSimulator API Server.
"""
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import DATABASE_URL

# Register UUID adapter
psycopg2.extras.register_uuid()


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor(commit=True):
    """Context manager for database cursor."""
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ============================================================
# Player operations
# ============================================================

def create_player(name: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO players (name) VALUES (%s) RETURNING *;",
            (name,)
        )
        return dict(cur.fetchone())


def get_player(player_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM players WHERE id = %s;", (player_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_players(limit: int = 50, offset: int = 0) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM players ORDER BY created_at DESC LIMIT %s OFFSET %s;",
            (limit, offset)
        )
        return [dict(row) for row in cur.fetchall()]


# ============================================================
# Team operations
# ============================================================

def create_team(player_id: str, name: str, pokemon_data: list) -> dict:
    import json
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO teams (player_id, name, pokemon_json) VALUES (%s, %s, %s) RETURNING *;",
            (player_id, name, json.dumps(pokemon_data))
        )
        return dict(cur.fetchone())


def get_team(team_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM teams WHERE id = %s;", (team_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_teams(player_id: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
    with get_cursor() as cur:
        if player_id:
            cur.execute(
                "SELECT * FROM teams WHERE player_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s;",
                (player_id, limit, offset)
            )
        else:
            cur.execute(
                "SELECT * FROM teams ORDER BY created_at DESC LIMIT %s OFFSET %s;",
                (limit, offset)
            )
        return [dict(row) for row in cur.fetchall()]


def delete_team(team_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute("DELETE FROM teams WHERE id = %s;", (team_id,))
        return cur.rowcount > 0


# ============================================================
# Battle operations
# ============================================================

def create_battle_record(
    battle_id: str,
    player_a_id: str | None,
    player_b_id: str | None,
    team_a_id: str | None,
    team_b_id: str | None,
    seed: int,
    init_json: dict,
) -> dict:
    import json
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO battles (id, player_a_id, player_b_id, team_a_id, team_b_id,
               seed, status, init_json)
               VALUES (%s, %s, %s, %s, %s, %s, 'active', %s) RETURNING *;""",
            (battle_id, player_a_id, player_b_id, team_a_id, team_b_id,
             seed, json.dumps(init_json))
        )
        return dict(cur.fetchone())


def update_battle_status(battle_id: str, status: str, winner_side: str = None,
                         winner_player_id: str = None, total_turns: int = None):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE battles SET status = %s,
               winner_side = COALESCE(%s, winner_side),
               winner_player_id = COALESCE(%s, winner_player_id),
               total_turns = COALESCE(%s, total_turns),
               completed_at = CASE WHEN %s = 'completed' THEN NOW() ELSE completed_at END
               WHERE id = %s;""",
            (status, winner_side, winner_player_id, total_turns, status, battle_id)
        )


def get_battle(battle_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM battles WHERE id = %s;", (battle_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_battles(status: str = None, player_id: str = None,
                 limit: int = 50, offset: int = 0) -> list[dict]:
    with get_cursor() as cur:
        conditions = []
        params = []
        if status:
            conditions.append("status = %s")
            params.append(status)
        if player_id:
            conditions.append("(player_a_id = %s OR player_b_id = %s)")
            params.extend([player_id, player_id])

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM battles{where} ORDER BY created_at DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def add_battle_turn(battle_id: str, turn_number: int, hdfs_path: str = None):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO battle_turns (battle_id, turn_number, hdfs_path)
               VALUES (%s, %s, %s)
               ON CONFLICT (battle_id, turn_number) DO UPDATE SET hdfs_path = %s;""",
            (battle_id, turn_number, hdfs_path, hdfs_path)
        )
