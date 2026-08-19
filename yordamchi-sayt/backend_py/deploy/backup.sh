#!/bin/bash
# Yordamchi — PostgreSQL bazasining kunlik zaxirasi.
# systemd timer (yordamchi-backup.timer) orqali har kuni ishga tushadi.
# O'rnatilgan joyi: /opt/yordamchi/backup.sh   Zaxiralar: /opt/yordamchi/backups/
set -euo pipefail

DB="${DB_NAME:-yordamchi}"
BACKUP_DIR="${BACKUP_DIR:-/opt/yordamchi/backups}"
KEEP="${KEEP_DAYS:-14}"          # nechta oxirgi zaxira saqlanadi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y-%m-%d_%H%M)"
FILE="$BACKUP_DIR/${DB}_${STAMP}.sql.gz"

# --- Zaxira olish ---
pg_dump "$DB" | gzip -9 > "$FILE"

# --- Tekshiruv: fayl haqiqatan ham to'ldimi? ---
# (bo'sh/buzuq zaxira eng yomon holat — borga o'xshaydi, lekin tiklab bo'lmaydi)
SIZE="$(stat -c%s "$FILE")"
if [ "$SIZE" -lt 1000 ]; then
    echo "XATO: zaxira juda kichik ($SIZE bayt) — o'chirildi." >&2
    rm -f "$FILE"
    exit 1
fi
if ! gzip -t "$FILE" 2>/dev/null; then
    echo "XATO: zaxira fayli buzuq (gzip test o'tmadi) — o'chirildi." >&2
    rm -f "$FILE"
    exit 1
fi

# --- Eski zaxiralarni tozalash (oxirgi $KEEP tasi qoladi) ---
ls -1t "$BACKUP_DIR/${DB}"_*.sql.gz 2>/dev/null | tail -n "+$((KEEP + 1))" | while read -r old; do
    rm -f "$old"
done

COUNT="$(ls -1 "$BACKUP_DIR/${DB}"_*.sql.gz 2>/dev/null | wc -l)"
echo "OK: $FILE ($(numfmt --to=iec "$SIZE")) — jami $COUNT ta zaxira saqlanmoqda."
