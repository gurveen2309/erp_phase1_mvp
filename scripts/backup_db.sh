#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [[ "${USE_POSTGRES:-0}" == "1" ]]; then
  : "${POSTGRES_DB:=erp_phase1}"
  : "${POSTGRES_USER:=erp}"
  : "${POSTGRES_PASSWORD:=erp}"
  : "${POSTGRES_HOST:=localhost}"
  : "${POSTGRES_PORT:=5432}"
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/db_$TIMESTAMP.sql"
else
  cp "$ROOT_DIR/db.sqlite3" "$BACKUP_DIR/db_$TIMESTAMP.sqlite3"
fi

echo "Backup created in $BACKUP_DIR"
