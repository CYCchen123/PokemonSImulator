"""
HDFS client for reading/writing battle data.
Uses WebHDFS REST API (no Hadoop native libraries needed).
"""
import json
import logging
import httpx
from datetime import datetime
from config import HDFS_NAMENODE, HDFS_PORT, HDFS_USER, HDFS_BASE_PATH

logger = logging.getLogger(__name__)

WEBHDFS_BASE = f"http://{HDFS_NAMENODE}:{HDFS_PORT}/webhdfs/v1"


def _webhdfs_url(path: str, op: str, **params) -> str:
    """Build a WebHDFS URL."""
    base = f"{WEBHDFS_BASE}{path}?user.name={HDFS_USER}&op={op}"
    for k, v in params.items():
        base += f"&{k}={v}"
    return base


async def _put_file(path: str, content: str, overwrite: bool = True) -> bool:
    """Upload a file to HDFS via WebHDFS (two-step: create + write)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Create file (get datanode redirect URL)
            create_url = _webhdfs_url(path, "CREATE", overwrite=str(overwrite).lower())
            resp = await client.put(create_url, follow_redirects=False)
            if resp.status_code not in (200, 201, 307):
                # 307 = redirect to datanode (expected)
                logger.error(f"HDFS CREATE failed: {resp.status_code} {resp.text[:200]}")
                return False

            # Step 2: Write data to datanode
            write_url = resp.headers.get("Location", create_url)
            resp2 = await client.put(write_url, content=content.encode('utf-8'))
            if resp2.status_code not in (200, 201):
                logger.error(f"HDFS WRITE failed: {resp2.status_code} {resp2.text[:200]}")
                return False

            logger.info(f"HDFS uploaded: {path} ({len(content)} bytes)")
            return True
        except Exception as e:
            logger.error(f"HDFS error: {e}")
            return False


async def _mkdir(path: str) -> bool:
    """Create a directory in HDFS."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            url = _webhdfs_url(path, "MKDIRS")
            resp = await client.put(url)
            return resp.status_code in (200, 201)
        except Exception as e:
            logger.error(f"HDFS MKDIRS error: {e}")
            return False


async def _get_file(path: str) -> str | None:
    """Read a file from HDFS."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = _webhdfs_url(path, "OPEN")
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return None
            return resp.text
        except Exception as e:
            logger.error(f"HDFS read error: {e}")
            return None


def _battle_path(battle_id: str) -> str:
    """Build the HDFS path for a battle's directory."""
    now = datetime.now()
    return f"{HDFS_BASE_PATH}/raw/battles/{now.year}/{now.month:02d}/{now.day:02d}/{battle_id}"


async def store_battle_init(battle_id: str, init_json: dict) -> bool:
    """Store battle initialization data to HDFS."""
    path = _battle_path(battle_id)
    await _mkdir(path)
    return await _put_file(f"{path}/init.json", json.dumps(init_json, ensure_ascii=False, indent=2))


async def store_battle_turn(battle_id: str, turn_number: int, state_json: dict) -> bool:
    """Store a single turn's state to HDFS."""
    path = _battle_path(battle_id)
    await _mkdir(path)
    filename = f"turn_{turn_number:03d}.json"
    return await _put_file(
        f"{path}/{filename}",
        json.dumps(state_json, ensure_ascii=False, indent=2)
    )


async def store_game_over(battle_id: str, summary: dict) -> bool:
    """Store game over summary to HDFS."""
    path = _battle_path(battle_id)
    return await _put_file(f"{path}/game_over.json", json.dumps(summary, ensure_ascii=False, indent=2))


async def get_battle_init(battle_id: str, date_hint: str = None) -> dict | None:
    """Read battle init data from HDFS."""
    # Try to find the battle by scanning date directories
    # For now, use the current date as default
    if date_hint:
        path = f"{HDFS_BASE_PATH}/raw/battles/{date_hint}/{battle_id}/init.json"
    else:
        path = _battle_path(battle_id) + "/init.json"

    content = await _get_file(path)
    return json.loads(content) if content else None


async def get_battle_turn(battle_id: str, turn_number: int, date_hint: str = None) -> dict | None:
    """Read a specific turn from HDFS."""
    if date_hint:
        path = f"{HDFS_BASE_PATH}/raw/battles/{date_hint}/{battle_id}/turn_{turn_number:03d}.json"
    else:
        path = _battle_path(battle_id) + f"/turn_{turn_number:03d}.json"

    content = await _get_file(path)
    return json.loads(content) if content else None
