#!/bin/bash
# Battle Engine entrypoint for JSON-file-based worker mode.
#
# The Python bridge writes input files to /workdir/cache/input/
# and reads results from /workdir/cache/output/
#
# This script runs the battle engine in daemon mode, polling for inputs.

set -e

echo "[engine] PokemonSimulator Battle Engine starting..."
echo "[engine] Mode: $ENGINE_MODE"
echo "[engine] Working directory: $(pwd)"

# Ensure cache directories exist
mkdir -p cache/input cache/output

case "${ENGINE_MODE:-daemon}" in
    daemon)
        echo "[engine] Starting in daemon mode (polling cache/input/)..."
        exec /usr/local/bin/PokemonSimulator --daemon
        ;;
    single)
        echo "[engine] Running single turn JSON file mode..."
        exec /usr/local/bin/PokemonSimulator \
            --run-turn-json-files \
            "${SIDE_A_FILE:-cache/input/side_a.json}" \
            "${SIDE_B_FILE:-cache/input/side_b.json}" \
            "${TURN_FILE:-cache/input/turn.json}" \
            "${SEED:-0}"
        ;;
    batch)
        echo "[engine] Running cache input batch mode..."
        exec /usr/local/bin/PokemonSimulator --run-cache-input
        ;;
    *)
        echo "[engine] Unknown ENGINE_MODE: $ENGINE_MODE"
        exit 1
        ;;
esac
