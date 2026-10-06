#!/usr/bin/env bash
# Kino bot — Hetzner (Ubuntu) uchun to'liq avtomat o'rnatish.
# Ishlatish (server ichida):  sudo bash deploy.sh
set -euo pipefail

APP_DIR="/opt/kino"
DB_NAME="kino"
DB_USER="kino"
DB_PASS="190919"

echo "==> 1/6 Paketlar"
apt-get update -y
apt-get install -y python3-venv python3-pip postgresql ufw

echo "==> 2/6 PostgreSQL bazasi"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "==> 3/6 Virtual muhit + kutubxonalar"
cd "${APP_DIR}"
# Python 3.14 da asyncpg/pydantic wheel yo'q — 3.12 ishlatamiz (subtitr ham shunday)
PYBIN="$(command -v python3.12 || command -v python3.13 || command -v python3)"
echo "    Python: ${PYBIN}"
rm -rf .venv
"${PYBIN}" -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

echo "==> 4/6 .env (agar yo'q bo'lsa namunadan)"
[ -f .env ] || cp .env.example .env
echo "    !!! .env ni tekshiring (token, WEB_BRIDGE_SECRET) !!!"

echo "==> 5/6 Eski ma'lumotni ko'chirish (agar JSON bor bo'lsa)"
if [ -f kino_export.json ]; then
  ./.venv/bin/python migrate_from_json.py kino_export.json || echo "    (import allaqachon bajarilgan bo'lishi mumkin)"
fi

echo "==> 6/6 systemd xizmati"
cat > /etc/systemd/system/kinobot.service <<EOF
[Unit]
Description=Kino Telegram Bot
After=network.target postgresql.service

[Service]
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now kinobot

# Web-admin faqat 127.0.0.1:8090 da (WEB_HOST=127.0.0.1) — master subtitr panel
# uni localhost orqali proxy qiladi. Portni internetga ochish SHART EMAS.

echo ""
echo "✅ TAYYOR. Holat:  systemctl status kinobot --no-pager"
echo "   Loglar:        journalctl -u kinobot -f"
echo "   Web-admin:     http://$(hostname -I | awk '{print $1}'):8080/admin"
