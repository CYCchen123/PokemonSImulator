# PokemonSimulator — 宝可梦对战大数据平台

C++17 宝可梦第九世代单打对战引擎 + 完整大数据生态 (Docker / Kafka / HDFS / Spark / Vue)。

---

## 架构

```
Vue 3 前端 (Nginx:80) ──► FastAPI (8000) ──► Kafka (9092) ──► C++ Battle Engine
                                │                    │
                                ▼                    ▼
                          PostgreSQL (5432)   HDFS 集群 (1NN+2DN)
                                                   │
                                                   ▼
                                              Apache Spark
                                         (批量分析 + 流式计算)
```

## 快速开始

### 1. 构建 C++ 引擎

```bash
cmake -B build -S . -G Ninja -DBUILD_TESTING=ON
cmake --build build

# 运行测试
ctest --test-dir build --output-on-failure
```

### 2. 启动大数据平台

```bash
# 启动全部基础设施 (HDFS 1NN+2DN + Kafka + PostgreSQL + API Server)
make up

# 初始化 HDFS 目录
make hdfs-init

# 检查状态
make status
```

### 3. 启动前端开发服务器

```bash
cd frontend && npm install && npm run dev
# 打开 http://localhost:5173
```

### 4. 启动 Spark 分析 (可选)

```bash
make up-analytics
docker exec pokemon-spark-master /opt/spark/jobs/submit.sh pokemon-usage
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Vue 前端 (dev) | 5173 | Vite 开发服务器 |
| Nginx (prod) | 80 | 前端静态 + API 代理 |
| API Server | 8000 | FastAPI REST |
| Kafka | 9092 | 消息代理 |
| NameNode Web UI | 9870 | HDFS 管理界面 |
| DataNode 1 Web UI | 9864 | DataNode 状态 |
| PostgreSQL | 5432 | 运营数据库 |
| Spark Master | 8080 | Spark 管理界面 (profile: analytics) |

## Kafka Topics

| Topic | 分区 | 保留 | 说明 |
|-------|------|------|------|
| `battle.requests` | 3 | 7天 | 对战请求 (create / turn) |
| `battle.results` | 3 | 7天 | 回合结果状态 |
| `battle.events` | 6 | 30天 | 细粒度对战事件 |
| `battle.analytics` | 3 | 永久 | Spark 分析结果 |

## HDFS 目录结构

```
/user/pokemon/
├── raw/battles/YYYY/MM/DD/{battle_id}/
│   ├── init.json
│   ├── turn_001.json
│   └── game_over.json
├── raw/events/YYYY/MM/DD/{battle_id}_events.jsonl
└── analytics/
    ├── pokemon_usage/
    ├── move_usage/
    ├── type_matchups/
    └── player_stats/
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST/GET | `/api/v1/players[/{id}]` | 玩家管理 |
| POST/GET/DELETE | `/api/v1/teams[/{id}]` | 队伍管理 |
| POST | `/api/v1/battles` | 创建对战 |
| POST | `/api/v1/battles/{id}/turns` | 处理回合 |
| GET | `/api/v1/battles[/{id}]` | 查询对战 |
| GET | `/api/v1/stats/global` | 全局统计 |
| GET | `/api/v1/data/enums` | 枚举映射 |

## C++ 引擎 CLI

```bash
./build/PokemonSimulator --help

# 运行模式:
--daemon                  # 守护进程 (轮询 cache/input/)
--run-cache-input         # 批量处理 cache/input/ 中的回合
--run-turn-json <file>    # 单回合 JSON 处理
--run-move-tests          # 招式测试
--run-item-tests          # 道具测试
--prefetch-moves          # 从 PokeAPI 预取招式数据
```

## 数据流

### 对战流程
```
1. Vue POST /api/v1/battles → API Server → Kafka battle.requests → C++ Engine
2. Engine 计算 → Kafka battle.results + battle.events → API Server 消费 → PostgreSQL
3. Kafka → HDFS Sink → HDFS 分布式存储
4. Spark 批量读取 HDFS → 聚合分析 → PostgreSQL 统计表
```

### 分析流程
```
Spark 批量: HDFS raw/ → PySpark DataFrame → 使用率/胜率 → PostgreSQL
Spark 流式: Kafka battle.events → 窗口聚合 → Kafka battle.analytics → API Server
```

## 项目结构

```
PokemonSimulator/
├── src/                    # C++ 引擎 (battle core + IO)
├── include/                # C++ 头文件
├── data/                   # 静态数据 (species/moves/abilities/items.json)
├── tests/                  # GTest 测试
├── api-server/             # Python FastAPI + Kafka Bridge
│   ├── main.py             # REST API 入口
│   ├── bridge_service.py   # Kafka ↔ C++ Engine 桥接
│   └── services/           # DB / Kafka / HDFS 客户端
├── spark-jobs/             # PySpark 分析任务
│   ├── batch/              # 批量分析
│   └── streaming/          # 流式分析
├── frontend/               # Vue 3 + Tailwind CSS
│   └── src/
│       ├── views/          # 7 个页面
│       ├── components/     # 9 个组件
│       ├── stores/         # 3 个 Pinia Store
│       └── utils/          # 枚举/格式化/精灵图工具
├── docker/                 # Docker 编排
│   ├── docker-compose.yml  # 9 服务编排
│   ├── hadoop/             # HDFS NameNode + DataNode
│   ├── kafka/              # Topic 初始化
│   ├── battle-engine/      # C++ 引擎容器
│   ├── api-server/         # Python API 容器
│   ├── spark/              # Spark 作业提交
│   └── nginx/              # 前端静态服务
├── third_party/            # cpp-httplib + sqlite3
└── Makefile                # 一键操作
```

## C++ 引擎覆盖

| 系统 | 状态 |
|------|------|
| 招式 | 277/277 变化招式 |
| 特性 | ~246 对战特性 |
| 道具 | 145 对战道具 (已冻结) |
| 天气 | 晴天/雨天/沙暴/冰雹/雪天 |
| 场地 | 精神/电气/青草/薄雾/戏法空间 |
| 状态 | 灼伤/麻痹/中毒/剧毒/睡眠/冰冻/畏缩/混乱 |

## 技术栈

| 层 | 技术 |
|----|------|
| 引擎 | C++17, CMake, Ninja, nlohmann/json |
| 消息 | Apache Kafka (Confluent 7.6) |
| 存储 | HDFS 3.3.6 (1NN+2DN), PostgreSQL 16 |
| 分析 | Apache Spark 3.5 (PySpark) |
| API | Python 3.12, FastAPI, kafka-python |
| 前端 | Vue 3, Vite, Tailwind CSS, Pinia, Chart.js |
| 部署 | Docker Compose, Nginx |

## 许可

MIT
