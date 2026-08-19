#!/bin/bash
# Mustaqil bot — shamsiyev serveriga deploy skripti
# Ishlatish: bash deploy.sh
set -e

PROJ=/opt/mustaqilbot
BOT_SERVICE=mustaqilbot
DB_USER=mustaqil
DB_PASS="Mustaqil_Pg2026!"
DB_NAME=mustaqilbot

echo "=== 1. Papka yaratish ==="
sudo mkdir -p $PROJ
sudo chown opc:opc $PROJ

echo "=== 2. Kod ko'chirish (lokal papkadan) ==="
# Bu qatorni o'chiring agar git clone ishlatsangiz
# Lokal: scp -i oracle_ssh -r . opc@141.147.156.65:/tmp/mustaqilbot_src
# Serverda:
# rsync -av /tmp/mustaqilbot_src/ /opt/mustaqilbot/

echo "=== 3. Python venv ==="
cd $PROJ
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 4. PostgreSQL baza ==="
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

echo "=== 5. .env fayli ==="
if [ ! -f $PROJ/.env ]; then
    cp $PROJ/.env.example $PROJ/.env
    echo "⚠️  $PROJ/.env faylini tahrirlang: ANTHROPIC_API_KEY va boshqalar"
fi

echo "=== 6. Systemd servis ==="
sudo tee /etc/systemd/system/$BOT_SERVICE.service > /dev/null << 'EOF'
[Unit]
Description=Mustaqil Ish Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=opc
WorkingDirectory=/opt/mustaqilbot
ExecStart=/opt/mustaqilbot/.venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable $BOT_SERVICE

echo "=== 7. Nginx konfiguratsiya ==="
echo "⚠️  MUHIM: /etc/nginx/conf.d/sessiyabot.conf ichidagi server {} blokiga"
echo "    quyidagi location'ni qo'shing (location /admin dan OLDIN):"
cat << 'EOF'

    # Mustaqil ish bot (talaba xizmatlari)
    location /mustaqil/ {
        proxy_pass http://127.0.0.1:8092/mustaqil/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
        client_max_body_size 50M;
    }

EOF
echo "    So'ng: sudo nginx -t && sudo systemctl reload nginx"

echo "=== 8. DB jadvallar ==="
cd $PROJ
source .venv/bin/activate
python -c "import asyncio; from db.crud import create_tables; asyncio.run(create_tables())"

echo "=== 9. Bot ishga tushirish ==="
sudo systemctl start $BOT_SERVICE
sleep 3
sudo systemctl status $BOT_SERVICE --no-pager

echo ""
echo "✅ Deploy tugadi!"
echo "Loglar: journalctl -u $BOT_SERVICE -f"
echo ".env tahrirlash: nano $PROJ/.env"
