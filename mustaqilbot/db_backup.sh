#!/bin/bash
# Mustaqilbot DB kunlik zaxira nusxasi (pg_dump + gzip, 7 kun saqlanadi).
# Cron orqali kuniga bir marta ishlaydi. Zaif serverga mos — kichik, tez.
set -e

BACKUP_DIR=/opt/mustaqilbot/_backups/db
DB_NAME=mustaqilbot
DB_USER=mustaqil
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M)
OUT="$BACKUP_DIR/mustaqilbot_$STAMP.sql.gz"

# Parol .pgpass yoki PGPASSWORD orqali (cron muhitida)
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$OUT"

# 7 kundan eski zaxiralarni o'chirish
find "$BACKUP_DIR" -name "mustaqilbot_*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "$(date '+%F %T') backup OK: $OUT ($(du -h "$OUT" | cut -f1))"
