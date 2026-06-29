# API Server + Bridge Service
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash pokemon && chown -R pokemon:pokemon /app
USER pokemon

EXPOSE 8000

# Start both API server and Kafka bridge consumer
CMD ["sh", "-c", "python bridge_service.py & python -m uvicorn main:app --host 0.0.0.0 --port 8000"]
