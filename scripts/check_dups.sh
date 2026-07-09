#!/bin/bash
python3 -c "
import sqlite3
db=sqlite3.connect('/home/hadoop/data/output.db')

# 重复检查
dups=db.execute('''
  SELECT battle_id,species_id,side_index,COUNT(*) c
  FROM battle_pokemon_states
  GROUP BY battle_id,species_id,side_index HAVING c>1
  LIMIT 10
''').fetchall()
if dups:
  print('=== 重复数据 ===')
  for bid,sid,si,c in dups:
    print(f'  battle={bid} species={sid} side={si}: {c}次')
else:
  print('无重复')

# 统计
total=db.execute('SELECT COUNT(*) FROM battle_pokemon_states').fetchone()[0]
battles=db.execute('SELECT COUNT(DISTINCT battle_id) FROM battle_pokemon_states').fetchone()[0]
species=db.execute('SELECT COUNT(DISTINCT species_id) FROM battle_pokemon_states').fetchone()[0]
print(f'总计: {total}行, {battles}场, {species}种精灵')

# 每个精灵平均出现次数
avg=db.execute('SELECT AVG(c) FROM (SELECT COUNT(*) c FROM battle_pokemon_states GROUP BY species_id)').fetchone()[0]
print(f'平均每精灵: {avg:.1f}次')
"
