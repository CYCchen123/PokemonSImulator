#!/bin/bash
# ============================================================
# PokemonSimulator 深度分析一键脚本
#
# 流程:
#   1. C++ 引擎运行 cache/input/ 中的对战回合
#   2. 复制输出到 battle_logs/
#   3. 运行 Spark 深度分析
#   4. 结果输出到 logs/analytics/
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok() { echo -e "${GREEN}  ✅ $1${NC}"; }
info() { echo -e "${YELLOW}  ℹ️  $1${NC}"; }

echo "========================================"
echo "  PokemonSimulator 深度分析"
echo "========================================"

# ── 1. 检查引擎是否已构建 ──────────────────────────
ENGINE="$PROJECT_DIR/build/PokemonSimulator"
if [ ! -f "$ENGINE" ]; then
    echo "  正在构建 C++ 引擎..."
    cmake --build build
fi

# ── 2. 运行 C++ 引擎处理所有 input ──────────────────
echo "[1/4] 运行 C++ 对战引擎..."
if ls "$PROJECT_DIR/cache/input/"*_input_*.json >/dev/null 2>&1; then
    "$ENGINE" --run-cache-input 2>&1 | tail -5
    ok "引擎完成 (查看 cache/output/)"
else
    info "无 input 文件，跳过对战模拟"
fi

# ── 3. 复制数据到 battle_logs/ ──────────────────────
echo "[2/4] 收集对战数据到 battle_logs/..."
mkdir -p battle_logs/input battle_logs/output

INPUT_COUNT=0
for f in cache/input/*_input_*.json; do
    [ -f "$f" ] || continue
    cp "$f" battle_logs/input/
    INPUT_COUNT=$((INPUT_COUNT + 1))
done

OUTPUT_COUNT=0
for f in cache/output/output_*.json; do
    [ -f "$f" ] || continue
    cp "$f" battle_logs/output/
    OUTPUT_COUNT=$((OUTPUT_COUNT + 1))
done

# Also copy side definitions if present
for f in cache/input/side_*.json; do
    [ -f "$f" ] || continue
    cp "$f" battle_logs/input/
done

ok "复制: ${INPUT_COUNT} 输入 + ${OUTPUT_COUNT} 输出"

if [ "$OUTPUT_COUNT" -eq 0 ]; then
    echo -e "${RED}  ❌ 无对战数据！请先运行对战生成输出。${NC}"
    exit 1
fi

# ── 4. 运行 Spark 分析 ──────────────────────────────
echo "[3/4] 运行 Spark 深度分析..."
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

OUTPUT_DIR="$PROJECT_DIR/logs/analytics"
mkdir -p "$OUTPUT_DIR"

# Run Spark analysis (local mode)
$VENV_PYTHON spark-jobs/batch/deep_analysis_job.py \
    --local --all \
    --battle-dir "$PROJECT_DIR/battle_logs" \
    --output-dir "$OUTPUT_DIR" \
    2>&1

ok "分析完成"

# ── 5. 列出结果 ─────────────────────────────────────
echo "[4/4] 结果文件:"
ls -lh "$OUTPUT_DIR"/*.csv "$OUTPUT_DIR"/*.json 2>/dev/null | awk '{print "  " $NF " (" $5 ")"}'

echo ""
echo "========================================"
echo -e "  ${GREEN}分析完成${NC}"
echo ""
echo "  结果目录: $OUTPUT_DIR"
echo ""
echo "  启动 API 查看:"
echo "    $VENV_PYTHON api-server/standalone_server.py"
echo "    curl http://localhost:8000/api/v1/stats/deep/meta"
echo ""
echo "  启动前端:"
echo "    cd frontend && npm run dev"
echo "========================================"
