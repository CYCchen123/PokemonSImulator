#!/usr/bin/env python3
"""
导入外部对战日志到项目 battle_logs/，按"初始上场"事件切分对战。

用法:
  python3 scripts/import_battles.py E:/Work/battle_logs/battle_logs

流程:
  1. 扫描 output/*.json，检测"初始上场"事件作为对战边界
  2. 将对战切分为独立的 battle_N
  3. 复制 output + input 文件到 battle_logs/<battle_id>/
  4. 运行 Spark 深度分析
"""

import json, os, sys, shutil, glob, re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATTLE_LOGS = PROJECT_ROOT / "battle_logs"


def parse_battle_groups(src_dir: str) -> list[list[int]]:
    """
    Scan output files and detect battle boundaries.
    Returns list of battle groups, each group = [turn_numbers...].
    A new battle starts when both sides have "初始上场" events.
    """
    output_dir = os.path.join(src_dir, "output")
    files = sorted(glob.glob(os.path.join(output_dir, "output_*.json")),
                   key=lambda f: int(re.search(r'output_(\d+)', f).group(1)))

    groups = []
    current_group = []

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        turn = data.get("turn", 0)
        events = data.get("events", [])

        # Check for initial send-out — marks a new battle
        has_initial = any(
            "初始上场" in e.get("description", "") or
            e.get("details", {}).get("reason") == "initial_send_out"
            for e in events
        )

        if has_initial and current_group:
            # Save previous group and start new one
            groups.append(current_group)
            current_group = [turn]
        else:
            current_group.append(turn)

    if current_group:
        groups.append(current_group)

    print(f"Found {len(groups)} battle(s) from {len(files)} output files")
    for i, g in enumerate(groups):
        print(f"  Battle {i+1}: turns {g[0]}-{g[-1]} ({len(g)} turns)")
    return groups


def import_data(src_dir: str):
    """Import battle data, split by initial send-out boundaries."""
    groups = parse_battle_groups(src_dir)

    # Clear existing battle_logs
    for d in BATTLE_LOGS.iterdir():
        if d.is_dir() and d.name != "input" and d.name != "output":
            shutil.rmtree(d, ignore_errors=True)
    # Also clear flat output dir if exists
    flat_output = BATTLE_LOGS / "output"
    if flat_output.exists():
        for f in flat_output.iterdir():
            f.unlink()
    flat_input = BATTLE_LOGS / "input"
    if flat_input.exists():
        for f in flat_input.iterdir():
            f.unlink()

    src_output = os.path.join(src_dir, "output")
    src_input = os.path.join(src_dir, "input")

    all_output_files = sorted(glob.glob(os.path.join(src_output, "output_*.json")),
                              key=lambda f: int(re.search(r'output_(\d+)', f).group(1)))
    all_input_files = sorted(glob.glob(os.path.join(src_input, "*_input_*.json")))

    for battle_idx, turn_list in enumerate(groups):
        battle_id = str(battle_idx + 1)
        bout_dir = BATTLE_LOGS / battle_id
        out_dir = bout_dir / "output"
        in_dir = bout_dir / "input"
        out_dir.mkdir(parents=True, exist_ok=True)
        in_dir.mkdir(parents=True, exist_ok=True)

        for turn in turn_list:
            # Copy output file
            src = os.path.join(src_output, f"output_{turn}.json")
            dst = out_dir / f"output_{turn}.json"
            if os.path.exists(src):
                shutil.copy2(src, dst)

            # Copy input files for this turn
            for in_file in all_input_files:
                base = os.path.basename(in_file)
                m = re.match(r'(\d+)_input_(\d+)\.json', base)
                if m and int(m.group(2)) == turn:
                    shutil.copy2(in_file, in_dir / base)

        print(f"  Battle {battle_id}: {len(turn_list)} turns imported")

    # Also put a flat copy of the first battle's inputs for side definitions
    if groups:
        first_battle = BATTLE_LOGS / "1" / "input"
        flat_in = BATTLE_LOGS / "input"
        flat_in.mkdir(exist_ok=True)
        for f in first_battle.iterdir():
            shutil.copy2(f, flat_in / f.name)


def run_analysis():
    """Run Spark deep analysis on imported data."""
    import subprocess
    venv_python = str(PROJECT_ROOT / "venv" / "bin" / "python3")
    if not os.path.exists(venv_python):
        venv_python = "python3"

    cmd = [
        venv_python,
        str(PROJECT_ROOT / "spark-jobs" / "batch" / "deep_analysis_job.py"),
        "--local", "--all",
        "--battle-dir", str(BATTLE_LOGS),
        "--output-dir", str(PROJECT_ROOT / "logs" / "analytics"),
    ]
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=False)
    return result.returncode == 0


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = str(PROJECT_ROOT / "battle_logs" / "battle_logs")

    if not os.path.isdir(src):
        print(f"Error: directory not found: {src}")
        print("Usage: python3 scripts/import_battles.py <path-to-battle-logs>")
        sys.exit(1)

    print(f"Importing from: {src}")
    import_data(src)

    print("\n" + "=" * 50)
    print("Running Spark analysis...")
    ok = run_analysis()
    if ok:
        print("Analysis complete! Results in logs/analytics/")
    else:
        print("Analysis had errors. Check output above.")


if __name__ == "__main__":
    main()
