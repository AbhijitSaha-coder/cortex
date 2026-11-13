#!/usr/bin/env bash
# ==============================================================================
# Generate secure production .env file with strong cryptographic secrets
# ==============================================================================
set -euo pipefail

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "Warning: .env file already exists at $(pwd)/$ENV_FILE"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting. Existing .env was preserved."
        exit 0
    fi
fi

echo "Generating cryptographically secure secrets..."
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)

cat <<EOF > "$ENV_FILE"
# ==============================================================================
# Cortex AI Research & Knowledge Agent - Production Environment Configuration
# Generated on: $(date -u +"%Y-%m-%d %H:%M:%SZ")
# ==============================================================================

# Application & Environment
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="Cortex — AI Research & Knowledge Agent"
ENABLE_API_DOCS=true

# Security
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Allowed CORS Origins (Frontend and API share origin via Nginx)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Database (PostgreSQL + pgvector)
POSTGRES_DB=cortex
POSTGRES_USER=cortex
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis & Celery Workers
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
TASK_ALWAYS_EAGER=false

# AI Reasoning Providers (Default: Gemini Free Tier)
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_EMBEDDING_PROVIDER=gemini

# Free Google Gemini API Key from: https://aistudio.google.com/
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# Optional paid keys:
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Embeddings
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=1536

# Ingestion Settings
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=25
CHUNK_SIZE=800
CHUNK_OVERLAP=150
DEFAULT_TOP_K=5
RRF_K=60

# Web Port
PORT=80

# Cloudflare Tunnel Token (optional)
CLOUDFLARE_TUNNEL_TOKEN=
EOF

chmod 600 "$ENV_FILE"
echo "Secure production .env created successfully with restricted permissions (chmod 600)."
echo "Edit .env to insert your GEMINI_API_KEY."

