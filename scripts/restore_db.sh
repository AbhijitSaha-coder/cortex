#!/usr/bin/env bash
# ==============================================================================
# Cortex Database Restore Script
# Usage: ./scripts/restore_db.sh <path_to_backup_file.sql.gz>
# ==============================================================================
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

echo "WARNING: Restoring will overwrite existing tables in the database."
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore aborted."
    exit 0
fi

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DB_USER="${POSTGRES_USER:-cortex}"
DB_NAME="${POSTGRES_DB:-cortex}"

echo "Restoring database from '$BACKUP_FILE'..."
gunzip -c "$BACKUP_FILE" | docker exec -i cortex_postgres psql -U "$DB_USER" -d "$DB_NAME"

echo "Database restored successfully!"

