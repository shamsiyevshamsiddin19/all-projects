#!/usr/bin/env bash
# Zenith Study Timer — Tezkor ishga tushirish skripti
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
INDEX="$DIR/index.html"

echo "⏱ Zenith Study Timer ishga tushirilmoqda..."

# Try opening in Chrome / Chromium app-mode if available, otherwise xdg-open
if command -v google-chrome &> /dev/null; then
  google-chrome --app="file://$INDEX" &
elif command -v chromium-browser &> /dev/null; then
  chromium-browser --app="file://$INDEX" &
elif command -v chromium &> /dev/null; then
  chromium --app="file://$INDEX" &
else
  xdg-open "$INDEX" &
fi
