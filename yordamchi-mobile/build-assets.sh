#!/usr/bin/env bash
# Saytni va ma'lumot suratini ilova ichiga ko'chiradi.
#
# NIMA UCHUN SKRIPT: `assets/www/` git'da SAQLANMAYDI — u yordamchi-sayt/
# dan olinadigan nusxa. Ikki joyda saqlansa, ular muqarrar bir-biridan
# uzoqlashib ketardi (saytda tuzatilgan xato ilovada qolib ketardi).
# Shuning uchun APK yasashdan oldin doim shu skript ishga tushiriladi.
set -euo pipefail
cd "$(dirname "$0")"

SITE="${YORDAMCHI_SITE:-$HOME/Documents/project/vibe-coding/yordamchi-sayt}"
[ -d "$SITE" ] || { echo "Sayt topilmadi: $SITE"; exit 1; }

rm -rf assets/www
mkdir -p assets/www assets/data
rsync -a \
  --exclude 'backend_py/' --exclude 'database/' --exclude 'yordamchi-app/' \
  --exclude 'assets/downloads/' --exclude 'uploads/' --exclude 'logs/' \
  --exclude 'tests/' --exclude 'deploy.sh' --exclude '.git*' --exclude '*.md' \
  --exclude 'assets/img/sport/' \
  "$SITE/" assets/www/
rsync -a "$SITE/assets/md_books/" assets/www/assets/md_books/

echo "Sayt ko'chirildi: $(du -sh assets/www | cut -f1)"
echo
echo "Ma'lumot surati (snapshot.json) serverdan olinadi — tools/make-snapshot.sh"
[ -f assets/data/snapshot.json ] && echo "Mavjud surat: $(du -h assets/data/snapshot.json | cut -f1)" \
  || echo "DIQQAT: assets/data/snapshot.json yo'q — ilova lug'atsiz chiqadi."
