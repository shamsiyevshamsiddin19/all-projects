#!/usr/bin/env bash
# RadioGlobe — serverga yoyish skripti.
#
# Birinchi marta ishga tushirishdan oldin:
#   cp .env.example .env   va barcha bo'sh qiymatlarni to'ldiring
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "❌ infra/.env topilmadi. Namuna: cp .env.example .env"
  exit 1
fi

# Bo'sh qolgan majburiy qiymatlarni oldindan tekshiramiz
missing=()
for key in POSTGRES_PASSWORD REDIS_PASSWORD PROXY_SECRET_KEY REVALIDATE_SECRET; do
  value="$(grep -E "^${key}=" .env | cut -d= -f2- || true)"
  [[ -z "$value" ]] && missing+=("$key")
done
if (( ${#missing[@]} )); then
  echo "❌ .env da quyidagilar bo'sh: ${missing[*]}"
  echo "   Yaratish: openssl rand -base64 32"
  exit 1
fi

echo "🔨 Образlar yig'ilmoqda..."
docker compose build

echo "🚀 Xizmatlar ishga tushirilmoqda..."
docker compose up -d

echo "⏳ API tayyor bo'lishini kutamiz..."
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null http://127.0.0.1:8000/api/v1/health; then
    echo "✅ API tayyor"
    break
  fi
  sleep 2
done

# Build paytida API mavjud bo'lmagani uchun bosh sahifa bo'sh prerender bo'ladi —
# uni darhol yangilaymiz
SECRET="$(grep -E '^REVALIDATE_SECRET=' .env | cut -d= -f2-)"
SITE="$(grep -E '^PUBLIC_SITE_URL=' .env | cut -d= -f2- || echo 'https://radio.shamsiyev.uz')"
echo "♻️  Bosh sahifa keshi yangilanmoqda..."
curl -fsS -X POST "${SITE}/api/revalidate?secret=${SECRET}" && echo || echo "⚠️  revalidate chaqiruvi o'tmadi"

echo
echo "📊 Holat:"
docker compose ps
