#!/usr/bin/env bash
# shamsiyev.uz saytini serverga yuklash.
#   ./deploy.sh [repo-yo'li]
# Repo ko'rsatilmasa, vaqtinchalik joyga GitHub'dan main klon qilinadi.
set -euo pipefail

HOST=shamsiyev-uz
REMOTE=/var/www/shamsiyev.uz
REPO_URL=https://github.com/shamsiyevshamsiddin19/shamsiyev.uz.git

SRC="${1:-}"
TMP=""
if [ -z "$SRC" ]; then
    TMP=$(mktemp -d)
    echo "==> main klon qilinmoqda..."
    git clone -q --depth 1 -b main "$REPO_URL" "$TMP/site"
    SRC="$TMP/site"
fi

echo "==> minify (npm run build)"
( cd "$SRC" && npm install --silent && npm run build )

echo "==> serverga yuborilmoqda ($HOST:$REMOTE)"
rsync -az --delete \
    --exclude .git --exclude node_modules --exclude functions \
    --exclude package.json --exclude package-lock.json --exclude _headers \
    --exclude README.md --exclude .gitignore \
    --rsync-path="sudo rsync" \
    "$SRC"/ "$HOST:$REMOTE"/

echo "==> ruxsatlar va nginx"
ssh "$HOST" '
    sudo chown -R nginx:nginx /var/www/shamsiyev.uz
    sudo chmod -R u=rwX,go=rX /var/www/shamsiyev.uz
    sudo restorecon -R /var/www/shamsiyev.uz 2>/dev/null || true
    sudo nginx -t && sudo systemctl reload nginx
'

[ -n "$TMP" ] && rm -rf "$TMP"
echo "==> TAYYOR: http://shamsiyev.uz"
