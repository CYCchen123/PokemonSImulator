.PHONY: help build test up down logs clean

# Default target
help:
	@echo "PokemonSimulator - Big Data Platform"
	@echo ""
	@echo "Build & Test (C++ Engine):"
	@echo "  make build          Build C++ engine"
	@echo "  make test           Run C++ tests"
	@echo "  make clean-build    Clean build artifacts"
	@echo ""
	@echo "Docker (Big Data Stack):"
	@echo "  make up             Start all services (HDFS + Kafka + PostgreSQL)"
	@echo "  make up-analytics   Start services + Spark analytics"
	@echo "  make up-frontend    Start services + Nginx frontend"
	@echo "  make down           Stop all services"
	@echo "  make logs           Tail all container logs"
	@echo "  make status         Show service status"
	@echo ""
	@echo "API Server (dev mode):"
	@echo "  make api            Start API server locally"
	@echo "  make bridge         Start bridge service locally"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-dev   Start Vue dev server"
	@echo "  make frontend-build Build Vue for production"
	@echo ""
	@echo "HDFS:"
	@echo "  make hdfs-ls        List HDFS root"
	@echo "  make hdfs-init      Initialize PokemonSimulator directories in HDFS"
	@echo ""

# ============================================================
# C++ Build
# ============================================================
build:
	cmake -B build -S . -G Ninja -DBUILD_TESTING=ON
	cmake --build build

test: build
	ctest --test-dir build --output-on-failure

clean-build:
	rm -rf build/

# ============================================================
# Docker
# ============================================================
up:
	docker compose -f docker/docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker compose -f docker/docker-compose.yml ps

up-analytics:
	docker compose -f docker/docker-compose.yml --profile analytics up -d
	@echo "Services + Spark started"
	@docker compose -f docker/docker-compose.yml ps

up-frontend:
	docker compose -f docker/docker-compose.yml --profile frontend up -d
	@echo "Services + Frontend started"

down:
	docker compose -f docker/docker-compose.yml --profile '*' down

logs:
	docker compose -f docker/docker-compose.yml logs -f --tail=50

status:
	docker compose -f docker/docker-compose.yml ps

# ============================================================
# API Server (local dev)
# ============================================================
api:
	cd api-server && pip install -r ../docker/api-server/requirements.txt
	cd api-server && python main.py

bridge:
	cd api-server && python bridge_service.py

# ============================================================
# Frontend
# ============================================================
frontend-dev:
	cd frontend && npm install && npm run dev

frontend-build:
	cd frontend && npm install && npm run build

# ============================================================
# HDFS
# ============================================================
hdfs-ls:
	docker exec pokemon-namenode hdfs dfs -ls /

hdfs-init:
	@echo "Creating HDFS directories for PokemonSimulator..."
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/raw/battles
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/raw/events
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/analytics/pokemon_usage
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/analytics/move_usage
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/analytics/type_matchups
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/analytics/player_stats
	docker exec pokemon-namenode hdfs dfs -mkdir -p /user/pokemon/models
	docker exec pokemon-namenode hdfs dfs -chmod -R 777 /user/pokemon
	@echo "HDFS directories created."

# ============================================================
# Kafka
# ============================================================
kafka-topics:
	docker exec pokemon-kafka kafka-topics --bootstrap-server kafka:9092 --list

kafka-logs:
	@echo "Consuming battle.requests (last 10 messages):"
	docker exec pokemon-kafka kafka-console-consumer --bootstrap-server kafka:9092 \
		--topic battle.requests --from-beginning --max-messages 10 2>/dev/null || true
	@echo ""
	@echo "Consuming battle.results (last 10 messages):"
	docker exec pokemon-kafka kafka-console-consumer --bootstrap-server kafka:9092 \
		--topic battle.results --from-beginning --max-messages 10 2>/dev/null || true

# ============================================================
# Database
# ============================================================
db-shell:
	docker exec -it pokemon-postgres psql -U pokemon -d pokemon_simulator

# ============================================================
# Clean
# ============================================================
clean: down
	rm -rf build/
	docker compose -f docker/docker-compose.yml down -v --remove-orphans
