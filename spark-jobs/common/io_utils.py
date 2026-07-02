"""
I/O utilities: path resolution, file listing, result writing.

Resolves data paths relative to POKEMON_ROOT (defaults to the
project root) so the pipeline works both locally and inside Docker.
"""

import os
import re
import json
from typing import List, Optional

# Project root – set via env or auto-detect from this file's location
POKEMON_ROOT = os.environ.get(
    "POKEMON_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
)


def resolve_path(*parts: str) -> str:
    """Resolve a path relative to POKEMON_ROOT."""
    return os.path.join(POKEMON_ROOT, *parts)


def list_json_files(subdir: str, pattern: Optional[str] = None) -> List[str]:
    """List all .json files under *subdir*, optionally filtered by glob."""
    import glob as gmod
    full = resolve_path(subdir, pattern or "*.json")
    return sorted(gmod.glob(full))


def extract_battle_id(filename: str) -> str:
    """Extract battle-id prefix from a battle-log filename.

    Examples:
        output_0.json  -> "0"
        1_input_5.json -> "1"
    """
    base = os.path.basename(filename)
    parent = os.path.basename(os.path.dirname(filename))
    # "output_N.json" format — if in subdir battle_logs/<id>/output/, use dir name
    m = re.match(r"output_(\d+)\.json$", base)
    if m:
        if parent == "output":
            grandparent = os.path.basename(os.path.dirname(os.path.dirname(filename)))
            if grandparent and grandparent not in ("battle_logs", "."):
                return grandparent
        return "1"  # fallback: single battle mode
    # "B_input_T.json" format -> battle_id = B (turn = T)
    m = re.match(r"(\d+)_input_\d+\.json$", base)
    if m:
        return m.group(1)
    return base.replace(".json", "")


def extract_turn(filename: str) -> int:
    """Extract turn number from a battle-log filename.

    Examples:
        output_5.json  -> 5
        1_input_3.json -> 3
    """
    base = os.path.basename(filename)
    m = re.match(r"output_(\d+)\.json$", base)
    if m:
        return int(m.group(1))
    m = re.match(r"\d+_input_(\d+)\.json$", base)
    if m:
        return int(m.group(1))
    return 0


def extract_bdata_info(filename: str):
    """Extract (period, cutoff) from BData filename.

    Example: 2025-07_gen91v1-1500.json -> ("2025-07", 1500)
    """
    base = os.path.basename(filename)
    m = re.match(r"(\d{4}-\d{2})_.*-(\d+)\.json$", base)
    if m:
        return m.group(1), int(m.group(2))
    return base[:7], 0


def write_output_csv(df, name: str, output_dir: str):
    """Write a Spark DataFrame to a single CSV file."""
    out = os.path.abspath(os.path.join(output_dir, f"{name}.csv"))
    df.coalesce(1).write.mode("overwrite") \
        .option("header", "true").csv(f"file://{out}")
    print(f"  [OK] {out}")


def write_output_json(data, name: str, output_dir: str):
    """Write a Python dict/list to a JSON file."""
    out = os.path.join(output_dir, f"{name}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {out}")
