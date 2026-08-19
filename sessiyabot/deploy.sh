#!/bin/bash
# shamsiyev'da sessiyabot deploy: PostgreSQL baza+user, pg_hba(md5), venv, import.
exec > /home/opc/deploy.log 2>&1
set -x
cd /home/opc/sessiyabot || exit 1

PASS=$(grep '^DATABASE_URL=' .env | sed -E 's#postgresql://sessiya:([^@]+)@.*#\1#')
DSN=$(grep '^DATABASE_URL=' .env | cut -d= -f2-)

# 1) PostgreSQL user + database (postgres superuser peer auth)
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='sessiya'" | grep -q 1 \
  || printf "CREATE USER sessiya WITH PASSWORD '%s';" "$PASS" | sudo -u postgres psql
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='sessiyabot'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE sessiyabot OWNER sessiya;"

# 2) pg_hba: 127.0.0.1 / ::1 uchun parol (md5) — bot/import TCP orqali ulanadi
PGHBA=$(sudo -u postgres psql -tAc "SHOW hba_file")
sudo sed -i -E 's#^(host[[:space:]]+all[[:space:]]+all[[:space:]]+127\.0\.0\.1/32[[:space:]]+)(ident|peer|trust)#\1md5#' "$PGHBA"
sudo sed -i -E 's#^(host[[:space:]]+all[[:space:]]+all[[:space:]]+::1/128[[:space:]]+)(ident|peer|trust)#\1md5#' "$PGHBA"
sudo systemctl reload postgresql
sleep 2

# 3) Python venv + bog'liqliklar (pip wheels — yengil)
python3 -m venv .venv
.venv/bin/pip install --upgrade pip >/dev/null 2>&1
.venv/bin/pip install -r requirements.txt

# 4) Sxema + ma'lumot import
.venv/bin/python import_data.py baza_export.json "$DSN" > /home/opc/import.log 2>&1
echo "=== IMPORT NATIJA ==="
cat /home/opc/import.log
echo "DEPLOY-DONE"
