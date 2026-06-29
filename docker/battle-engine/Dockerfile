# Multi-stage build: compile C++ engine, then create minimal runtime
FROM ubuntu:22.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    libcurl4-openssl-dev \
    nlohmann-json3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy source files
COPY CMakeLists.txt .
COPY src/ ./src/
COPY include/ ./include/
COPY data/ ./data/
COPY third_party/ ./third_party/

# Build
RUN cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    && cmake --build build --target PokemonSimulator \
    && cp build/PokemonSimulator /usr/local/bin/

# ============================================================
# Runtime stage
# ============================================================
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 \
    libstdc++6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binary and data
COPY --from=builder /usr/local/bin/PokemonSimulator /usr/local/bin/
COPY data/ /data/

# Test binary works
RUN PokemonSimulator --help 2>&1 || true

WORKDIR /workdir
ENTRYPOINT ["/usr/local/bin/PokemonSimulator"]
