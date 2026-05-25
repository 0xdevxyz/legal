#!/bin/bash
# rollback.sh - Complyo Rebuild Rollback
# Datum: 2026-05-22
# Ausführen bei: kritischem Fehler im Rebuild-Prozess

set -euo pipefail

REPO_ROOT="/home/clawd/saas/legal"
BACKUP_DATE="2026-05-22"
DB_CONTAINER="complyo-postgres"
DB_USER="complyo_user"
DB_NAME="complyo_db"
SCHEMA_BACKUP="$REPO_ROOT/data/system-stabilization-$BACKUP_DATE/00_baseline/db_schema_pre.sql"

echo "[ROLLBACK] Starting rollback to pre-rebuild-$BACKUP_DATE state..."

echo "[1/4] Switching git branch to main..."
cd "$REPO_ROOT"
git checkout main

echo "[2/4] Restarting Docker containers from main..."
docker compose down
docker compose up -d

echo "[3/4] Waiting for containers..."
sleep 10

echo "[4/4] Done. Verify manually:"
echo "  docker ps"
echo "  curl http://localhost:8002/health"

echo ""
echo "[ROLLBACK COMPLETE]"
echo "Branch: main"
echo "To restore DB schema (DESTRUCTIVE - only if schema was migrated):"
echo "  docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < $SCHEMA_BACKUP"
