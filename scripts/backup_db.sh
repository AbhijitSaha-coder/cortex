#!/usr/bin/env bash
# ==============================================================================
# Cortex Database Backup Script (PostgreSQL + pgvector)
# ==============================================================================
set -euo pipefail

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/cortex_backup_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating compressed PostgreSQL backup to: ${BACKUP_FILE}..."

# Source .env if present for credentials
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DB_USER="${POSTGRES_USER:-cortex}"
DB_NAME="${POSTGRES_DB:-cortex}"

docker exec -t cortex_postgres pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "Backup completed successfully!"
echo "Size: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

