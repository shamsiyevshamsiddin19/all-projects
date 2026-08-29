#!/usr/bin/env bash
#
# Yordamchi sayt — statik fayllarni serverga xavfsiz yuklash.
#
#   ./deploy.sh assets/js/app2/vocab.js assets/css/app.css
#   ./deploy.sh --all-changed          # git'da o'zgargan fayllarni o'zi topadi
#
# NIMA UCHUN SKRIPT KERAK
# =======================
# Qo'lda `scp` qilish ikki marta jiddiy nosozlikka olib keldi (2026-08-28/29):
#
# 1) KESH TUZOG'I. nginx statik fayllarni `Cache-Control: immutable,
#    max-age=1yil` bilan beradi. Faylni almashtirishning O'ZI yetmaydi —
#    brauzer eski nusxani abadiy ushlab qoladi. `index.html` dagi `?v=...`
#    belgisini HAM yangilash shart. Bir marta unutildi va hech kim
#    yangilanishni ko'rmadi.
#
# 2) YIRTIQ FAYL. `scp` faylni JOYIDA qayta yozadi. Shu payt brauzer o'sha
#    faylni so'rasa, nginx CHALA faylni beradi — va `immutable` tufayli
#    buzuq nusxa o'sha `?v=` manzili ostida abadiy keshlanadi. Sayt
#    butunlay ishlamay qoldi, `node --check` esa "OK" deb turaverdi,
#    chunki u boshqa faylni o'qiyotgan edi.
#
# Skript ikkalasini ham yopadi: sintaksisni oldindan tekshiradi, faylni
# vaqtinchalik nomga yuklab ATOMIK `mv` bilan almashtiradi, `?v=` va
# service-worker versiyasini birga yangilaydi, so'ng serverdan qaytarib
# o'qib hajmini solishtiradi.

set -euo pipefail

HOST="${YORDAMCHI_HOST:-opc@82.70.41.85}"
KEY="${YORDAMCHI_KEY:-$HOME/.ssh/oracle_yangi}"
ROOT="/opt/yordamchi/Yordamchisayt"
SSH=(ssh -i "$KEY" "$HOST")

cd "$(dirname "$0")"

# ---------- Yuklanadigan fayllar ----------
if [ "${1:-}" = "--all-changed" ]; then
  mapfile -t FILES < <(git status --porcelain . | awk '{print $NF}' \
    | grep -E '\.(js|css|html)$' | sed 's|^yordamchi-sayt/||')
else
  FILES=("$@")
fi

if [ ${#FILES[@]} -eq 0 ]; then
  echo "Yuklanadigan fayl ko'rsatilmadi."
  echo "Masalan: ./deploy.sh assets/js/app2/vocab.js"
  exit 1
fi

# ---------- 1. Oldindan tekshiruv ----------
# Buzuq fayl serverga umuman chiqmasin.
echo "== Tekshiruv =="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "  YO'Q: $f"; exit 1; }
  case "$f" in
    *.js)
      if command -v node >/dev/null 2>&1; then
        node --check "$f" >/dev/null || { echo "  SINTAKSIS XATO: $f"; exit 1; }
        echo "  ok  $f"
      else
        echo "  (node yo'q, $f tekshirilmadi)"
      fi
      ;;
    *.css)
      # Qavslar balansi — eng ko'p uchraydigan CSS nosozligi
      o=$(tr -cd '{' < "$f" | wc -c); c=$(tr -cd '}' < "$f" | wc -c)
      [ "$o" -eq "$c" ] || { echo "  QAVS BALANSI BUZUQ: $f ({=$o }=$c)"; exit 1; }
      echo "  ok  $f"
      ;;
    *) echo "  ok  $f" ;;
  esac
done

# ---------- 2. Yangi versiya belgisi ----------
VER="$(date +%Y%m%d)v$(date +%H%M%S)"
echo
echo "== Versiya: $VER =="

# ---------- 3. Atomik yuklash ----------
echo "== Yuklash =="
for f in "${FILES[@]}"; do
  scp -q -i "$KEY" "$f" "$HOST:$ROOT/$f.deploytmp"
  "${SSH[@]}" "mv -f '$ROOT/$f.deploytmp' '$ROOT/$f'"
  echo "  yuklandi  $f"
done

# ---------- 4. Kesh belgilarini yangilash ----------
# `?v=` FAQAT shu yuklangan fayllar uchun almashtiriladi — tegilmagan
# fayllarning keshini bekorga buzmaymiz.
echo "== Kesh belgilari =="
for f in "${FILES[@]}"; do
  base="${f#assets/}"
  "${SSH[@]}" "sed -i 's|\(${base//\//\\/}\)?v=[^\"]*|\1?v=$VER|g' '$ROOT/index.html'"
  echo "  ?v=$VER  $base"
done
"${SSH[@]}" "sed -i \"s/^const VERSION = .*/const VERSION = '$VER';/\" '$ROOT/service-worker.js'"
echo "  service-worker VERSION=$VER"

# ---------- 5. Serverdan qaytarib tekshirish ----------
# Yirtiq fayl aynan shu bosqichda ushlanadi.
echo "== Tasdiqlash =="
fail=0
for f in "${FILES[@]}"; do
  local_size=$(stat -c%s "$f")
  remote_size=$("${SSH[@]}" "stat -c%s '$ROOT/$f'")
  if [ "$local_size" = "$remote_size" ]; then
    echo "  ok  $f ($local_size bayt)"
  else
    echo "  HAJM MOS EMAS: $f  mahalliy=$local_size server=$remote_size"
    fail=1
  fi
done
[ "$fail" -eq 0 ] || { echo "XATO: yuklash to'liq bo'lmadi."; exit 1; }

echo
echo "Tayyor. Versiya: $VER"
echo "Brauzerda tekshiring: https://y.wstore.uz/"
