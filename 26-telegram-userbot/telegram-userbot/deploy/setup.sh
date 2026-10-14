#!/usr/bin/env bash
# Serverda bir marta ishga tushiriladi: kod, venv va kutubxonalarni tayyorlaydi.
# Ishlatish (server ichida):
#   bash /opt/telegram-userbot/deploy/setup.sh
set -e

APP_DIR="/opt/telegram-userbot"

echo ">>> Tizim dasturlari o'rnatilmoqda..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip

cd "$APP_DIR"

echo ">>> Virtual muhit yaratilmoqda..."
python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

if [ ! -f .env ]; then
    cp .env.example .env
    echo ">>> .env yaratildi — endi uni tahrirlang: nano $APP_DIR/.env"
else
    echo ">>> .env allaqachon mavjud."
fi

echo ""
echo "============================================"
echo "TAYYOR. Keyingi qadamlar:"
echo "  1) nano $APP_DIR/.env      # API_ID, API_HASH, GEMINI_API_KEY"
echo "  2) Har akkauntga login (bir martalik):"
echo "       venv/bin/python userbot.py acc1"
echo "       venv/bin/python userbot.py acc2"
echo "       venv/bin/python userbot.py acc3"
echo "  3) systemd xizmatlari:"
echo "       cp deploy/userbot@.service /etc/systemd/system/"
echo "       systemctl daemon-reload"
echo "       systemctl enable --now userbot@acc1 userbot@acc2 userbot@acc3"
echo "============================================"
