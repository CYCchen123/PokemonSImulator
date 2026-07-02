#!/bin/bash
set -e
cd ""/bin"
echo "========================================"
echo "  PokemonSimulator 一键启动"
echo "========================================"

# Setup
[ ! -d "venv" ] && python3 -m venv venv && venv/bin/pip install fastapi uvicorn -q
[ ! -d "frontend/node_modules" ] && (cd frontend && npm install --silent 2>/dev/null)

mkdir -p data logs battle_logs/input battle_logs/output cache/input cache/output

# Stop old
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true
sleep 1

# API
echo "[1/2] API Server..."
nohup venv/bin/python3 api-server/standalone_server.py > logs/api-server.log 2>&1 &
for i in 1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20; do
  sleep 0.5
  curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1 && echo "  API: http://localhost:8000" && break
done

# Frontend
echo "[2/2] Frontend..."
cd frontend && nohup npm run dev > ../logs/frontend.log 2>&1 &
for i in 1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20; do
  sleep 0.5
  curl -sf http://localhost:5173 >/dev/null 2>&1 && echo "  Web: http://localhost:5173" && break
done
cd ""/bin"

echo "========================================"
echo " 启动完成!"
echo " 测试数据: python3 scripts/gen_battle_stream.py --interval 10"
echo " 停止: fuser -k 8000/tcp 5173/tcp"
echo "========================================"
