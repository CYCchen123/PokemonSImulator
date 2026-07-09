#!/bin/bash
echo "=== Clearing all battle data ==="

# Stop processes
pkill -f SparkSubmit 2>/dev/null || true
pkill -f gen_battle_stream 2>/dev/null || true
sleep 2

# Check before
BEFORE=$(python3 -c "import sqlite3;db=sqlite3.connect('/home/hadoop/data/output.db');print(db.execute('SELECT COUNT(*) FROM battle_pokemon_states').fetchone()[0])")
BATTLES=$(python3 -c "import sqlite3;db=sqlite3.connect('/home/hadoop/data/output.db');print(db.execute('SELECT COUNT(DISTINCT battle_id) FROM battle_pokemon_states').fetchone()[0])")
echo "Before: $BEFORE rows ($BATTLES battles)"

# Clear DB
python3 -c "
import sqlite3
db=sqlite3.connect('/home/hadoop/data/output.db')
db.execute('DELETE FROM battle_pokemon_states')
db.commit()
print(f'Deleted {db.total_changes} rows')
"

# Verify
AFTER=$(python3 -c "import sqlite3;db=sqlite3.connect('/home/hadoop/data/output.db');print(db.execute('SELECT COUNT(*) FROM battle_pokemon_states').fetchone()[0])")
echo "After: $AFTER rows"

# Restart
~/start.sh

echo "=== Done ==="
