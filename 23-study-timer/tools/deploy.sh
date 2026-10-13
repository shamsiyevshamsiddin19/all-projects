#!/usr/bin/env bash
#
# Zenith Study Timer — timer.shamsiyev.uz ga deploy.
#
# Nima qiladi:
#   1. Faqat ishga kerakli fayllarni ajratadi (app.py, testlar, data/ serverga chiqmaydi).
#   2. Service worker versiyasini muhrlaydi — aks holda eski kesh yangi koddan ustun keladi.
#   3. Serverga rsync qiladi, huquqlarni va SELinux kontekstini tiklaydi.
#   4. Jonli saytni tekshiradi.
#
# Ishlatish:  ./tools/deploy.sh
set -euo pipefail

HOST="${ZENITH_HOST:-shamsiyev-uz}"
WEBROOT="${ZENITH_WEBROOT:-/var/www/timer.shamsiyev.uz}"
SITE="${ZENITH_SITE:-https://timer.shamsiyev.uz}"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cd "$DIR"

echo "⏱  Zenith deploy → $HOST:$WEBROOT"

# --- 1. Faqat ishga kerakli fayllar ---
cp index.html manifest.webmanifest sw.js "$STAGE"/
cp -r css js icons "$STAGE"/
find "$STAGE" -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# --- 2. Service worker versiyasini muhrlash ---
STAMP="$(date +%Y%m%d-%H%M)-$(git rev-parse --short HEAD 2>/dev/null || echo nogit)"
sed -i "s/^const VERSION = '\([^']*\)';/const VERSION = '\1-$STAMP';/" "$STAGE/sw.js"
echo "   SW versiyasi: $(grep -m1 '^const VERSION' "$STAGE/sw.js")"

FILES=$(find "$STAGE" -type f | wc -l)
echo "   Fayllar: $FILES ($(du -sh "$STAGE" | cut -f1))"

# --- 3. Yuklash ---
rsync -az --delete "$STAGE"/ "$HOST:/tmp/zenith_deploy/"

ssh "$HOST" "bash -s" <<REMOTE
set -e
sudo tar czf "\$HOME/timer-backup-\$(date +%Y%m%d-%H%M).tar.gz" -C "$WEBROOT" . 2>/dev/null || true
sudo rsync -a --delete /tmp/zenith_deploy/ "$WEBROOT/"
sudo chown -R nginx:nginx "$WEBROOT"
sudo restorecon -R "$WEBROOT" 2>/dev/null || true
rm -rf /tmp/zenith_deploy
sudo nginx -t >/dev/null && sudo systemctl reload nginx
REMOTE

# --- 4. Tekshirish ---
echo "   Tekshiruv:"
fail=0
for path in "" "sw.js" "manifest.webmanifest" "js/app.js" "js/engine/timer-engine.js" "icons/icon-192.png"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$SITE/$path")
  printf "     %-32s %s\n" "/$path" "$code"
  [ "$code" = "200" ] || fail=1
done
for path in "app.py" "test_all.py" "data/timer_data.json"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$SITE/$path")
  printf "     %-32s %s (404 kutilgan)\n" "/$path" "$code"
  [ "$code" = "404" ] || fail=1
done

if [ "$fail" -eq 0 ]; then
  echo "✅ Deploy muvaffaqiyatli: $SITE"
else
  echo "❌ Deployda muammo bor — yuqoridagi kodlarni tekshiring." >&2
  exit 1
fi
