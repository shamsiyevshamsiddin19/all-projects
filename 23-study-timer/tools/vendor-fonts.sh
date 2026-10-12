#!/usr/bin/env bash
# Shriftlarni loyihaga ko'chirish (to'liq oflayn rejim uchun, ixtiyoriy).
#
# Service worker shriftlarni birinchi yuklanishdan keyin keshlaydi, shu sabab bu skript
# faqat "hech qachon internetga chiqmasin" talabi bo'lsa kerak bo'ladi.
# Yuklab olingan fayllar: fonts/*.woff2 (~1–3 MB) + fonts/fonts.css
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
OUT="$DIR/fonts"
CSS_URL="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500&family=Montserrat:wght@100;200;300;400&family=Urbanist:wght@100;200;300;400;500&family=JetBrains+Mono:wght@100;200;300;400&family=Cormorant+Garamond:wght@300;400&display=swap"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

mkdir -p "$OUT"
echo "⬇  CSS olinmoqda ..."
curl -sL -A "$UA" "$CSS_URL" -o "$OUT/fonts.css"

echo "⬇  woff2 fayllari olinmoqda ..."
grep -oE 'https://fonts\.gstatic\.com[^)]+\.woff2' "$OUT/fonts.css" | sort -u | while read -r url; do
  name="$(basename "$url")"
  curl -sL -A "$UA" "$url" -o "$OUT/$name"
  # CSS ichidagi manzilni mahalliy faylga almashtiramiz
  sed -i "s|$url|./$name|g" "$OUT/fonts.css"
  echo "   ✓ $name"
done

cat <<'NOTE'

✅ Tayyor. Endi index.html dagi Google Fonts <link> larini quyidagiga almashtiring:

    <link rel="stylesheet" href="fonts/fonts.css">

NOTE
