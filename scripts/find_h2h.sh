#!/bin/bash
python3 -c "
import sqlite3
db=sqlite3.connect('/home/hadoop/data/output.db')
pairs=db.execute('''SELECT a.species_id s1,b.species_id s2,COUNT(DISTINCT a.battle_id) c
  FROM battle_pokemon_states a JOIN battle_pokemon_states b ON a.battle_id=b.battle_id
  WHERE a.species_id<b.species_id AND a.side_index!=b.side_index
  GROUP BY 1,2 HAVING c>=2 ORDER BY c DESC LIMIT 5''').fetchall()
poke=sqlite3.connect('/home/hadoop/pokemon.db')
n=dict(poke.execute('SELECT id,name FROM species').fetchall())
for s1,s2,c in pairs:
    print(f'{n.get(s1,s1)} vs {n.get(s2,s2)} — {c}场')
"
