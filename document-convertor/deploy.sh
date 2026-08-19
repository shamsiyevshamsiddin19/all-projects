#!/usr/bin/env bash
# Document Convertor bot — Hetzner (Ubuntu) uchun o'rnatish/yangilash skripti.
# Ishlatish (server ichida):  sudo bash deploy.sh
set -euo pipefail

APP_DIR="/root/bot_deploy"
DB_PASS="CHANGE_ME"

echo "==> 1/6 Paketlar (Python, PostgreSQL, LibreOffice, Tesseract OCR)"
apt-get update -y
apt-get install -y python3-venv python3-pip postgresql libreoffice tesseract-ocr \
  tesseract-ocr-uzb tesseract-ocr-rus tesseract-ocr-eng

echo "==> 2/6 PostgreSQL"
systemctl start postgresql
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '${DB_PASS}';" || true

echo "==> 3/6 Virtual muhit + kutubxonalar"
cd "${APP_DIR}"
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "==> 4/6 .env (agar yo'q bo'lsa namunadan)"
[ -f .env ] || cp .env.example .env
echo "    !!! .env ni tekshiring (BOT_TOKEN, DB_PASS, ADMIN_PASSWORD) !!!"

echo "==> 5/6 systemd xizmati"
cat > /etc/systemd/system/pdfbot.service <<EOF
[Unit]
Description=PdfZipMasterBot
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=${APP_DIR}/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
# Eslatma: PATH ga tizim yo'llari ATAYLAB qo'shilgan — subprocess orqali
# chaqiriladigan libreoffice/tesseract faqat venv/bin bo'lsa topilmaydi.

echo "==> 6/6 Xizmatni yoqish"
systemctl daemon-reload
systemctl enable --now pdfbot.service

echo ""
echo "✅ TAYYOR. Holat:  systemctl status pdfbot --no-pager"
echo "   Loglar:        journalctl -u pdfbot -f"
echo "   Web-admin:     http://$(hostname -I | awk '{print $1}'):8085/docs/admin"
