# ==============================================================================
# Cortex AI Research & Knowledge Agent - Unified Production Cloud Dockerfile
# ==============================================================================

# Stage 1: Build React + Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Unified Cloud Runtime
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (libpq-dev for Postgres, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./

# Copy compiled frontend SPA
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set permissions for non-root user (UID 1000 required for Hugging Face Spaces)
RUN useradd -m -u 1000 user && \
    mkdir -p /app/uploads && \
    chown -R user:user /app

# Copy startup script
COPY --chown=user:user scripts/start_cloud.sh /app/start_cloud.sh
RUN chmod +x /app/start_cloud.sh

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    FRONTEND_DIST=/app/frontend/dist

EXPOSE 7860

CMD ["/app/start_cloud.sh"]

