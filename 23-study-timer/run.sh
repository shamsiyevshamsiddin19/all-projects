#!/usr/bin/env bash
# Zenith Study Timer — ishga tushirish skripti.
#
# file:// orqali ochish ES modullarini, service worker'ni, bildirishnomalarni va
# JSON omborini ishlatmaydi. Shu sabab skript mahalliy serverni ishga tushiradi.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PORT="${ZENITH_PORT:-5050}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 topilmadi. O'rnating: sudo apt install python3" >&2
  exit 1
fi

echo "⏱  Zenith Study Timer ishga tushirilmoqda (http://localhost:${PORT}) ..."
exec python3 "$DIR/app.py" --port "$PORT" "$@"
