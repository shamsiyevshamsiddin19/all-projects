#!/usr/bin/env bash
#
# Yordamchi sayt — o'rnatish.
#
#   ./deploy.sh assets/js/app2/vocab.js assets/css/app.css
#   ./deploy.sh --all-changed          # git'da o'zgargan fayllarni o'zi topadi
#
# UCH MUAMMO SHU YERDA YOPILGAN
# =============================
#
# 1) KESH TUZOG'I. nginx statik fayllarni `immutable, max-age=1yil` bilan
#    beradi. Faylni almashtirishning O'ZI yetmaydi — `?v=` belgisi ham
#    yangilanishi shart. Bir marta unutildi va hech kim yangilanishni
#    ko'rmadi.
#
# 2) YIRTIQ FAYL. `scp` faylni JOYIDA qayta yozadi. Shu payt brauzer o'sha
#    faylni so'rasa, nginx CHALA faylni beradi — va `immutable` tufayli
#    buzuq nusxa abadiy keshlanadi. Sayt butunlay ishlamay qolgan edi,
#    `node --check` esa "OK" derdi, chunki u boshqa faylni o'qiyotgan edi.
#
# 3) ESKI VERSIYA OCHILISHI. Ilgari skript FAQAT serverdagi index.html va
#    service-worker.js ni tahrirlardi. Natijada git'dagi nusxa haqiqatni
#    aks ettirmasdi, va har fayl o'z `?v=` siga ega bo'lgani uchun kesh
#    holati chalkash edi. Endi BITTA build raqami hamma narsaga qo'yiladi
#    (index.html, service-worker.js, version.json) va MAHALLIY fayllar ham
#    yangilanadi — ya'ni git aynan o'rnatilgan holatni saqlaydi.
#
# `version.json` ni sahifa o'zi o'qib turadi (bootstrap.js -> guardVersion):
# serverdagi build sahifadagidan farq qilsa, keshlar tozalanib sahifa bir
# marta qayta yuklanadi. Shu sababli tarmoq uzilib eski nusxa ochilib
# qolsa ham, ilova ulanish tiklanishi bilan o'zi eng so'nggisiga o'tadi.

set -euo pipefail

HOST="${YORDAMCHI_HOST:-opc@82.70.41.85}"
KEY="${YORDAMCHI_KEY:-$HOME/.ssh/oracle_yangi}"
ROOT="/opt/yordamchi/Yordamchisayt"
SSH=(ssh -i "$KEY" "$HOST")

cd "$(dirname "$0")"

if [ "${1:-}" = "--all-changed" ]; then
  mapfile -t FILES < <(git status --porcelain . | awk '{print $NF}' \
    | grep -E '\.(js|css)$' | sed 's|^yordamchi-sayt/||')
else
  FILES=("$@")
fi

if [ ${#FILES[@]} -eq 0 ]; then
  echo "Yuklanadigan fayl ko'rsatilmadi."
  echo "Masalan: ./deploy.sh assets/js/app2/vocab.js"
  exit 1
fi

# ---------- 1. Oldindan tekshiruv ----------
echo "== Tekshiruv =="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "  YO'Q: $f"; exit 1; }
  case "$f" in
    *.js)
      if command -v node >/dev/null 2>&1; then
        node --check "$f" >/dev/null || { echo "  SINTAKSIS XATO: $f"; exit 1; }
      fi
      echo "  ok  $f" ;;
    *.css)
      o=$(tr -cd '{' < "$f" | wc -c); c=$(tr -cd '}' < "$f" | wc -c)
      [ "$o" -eq "$c" ] || { echo "  QAVS BALANSI BUZUQ: $f ({=$o }=$c)"; exit 1; }
      echo "  ok  $f" ;;
    *) echo "  ok  $f" ;;
  esac
done

# Testlar bor bo'lsa — buzuq kod serverga chiqmasin
if [ -f tests/run.js ] && command -v node >/dev/null 2>&1; then
  echo "== Testlar =="
  node tests/run.js | tail -1
fi

BUILD="$(date +%Y%m%d-%H%M%S)"
echo
echo "== Build: $BUILD =="

# ---------- 2. Mahalliy fayllarni yangilash ----------
# BITTA build hamma joyda: index.html dagi HAMMA `?v=`, SW VERSION va
# version.json. Shunda "qaysi fayl qaysi versiyada" degan savol yo'qoladi.
python3 - "$BUILD" <<'PY'
import re, sys, json, pathlib
build = sys.argv[1]

idx = pathlib.Path('index.html')
html = idx.read_text(encoding='utf-8')
html = re.sub(r'(\.(?:js|css|webmanifest))\?v=[^"\']*', r'\1?v=' + build, html)
html = re.sub(r'(<meta name="app-build" content=")[^"]*(")', r'\g<1>' + build + r'\g<2>', html)
idx.write_text(html, encoding='utf-8')

sw = pathlib.Path('service-worker.js')
sw.write_text(re.sub(r"^const VERSION = .*$",
                     "const VERSION = '%s';" % build,
                     sw.read_text(encoding='utf-8'), count=1, flags=re.M),
              encoding='utf-8')

pathlib.Path('version.json').write_text(
    json.dumps({"build": build}, ensure_ascii=False) + "\n", encoding='utf-8')
print("  index.html, service-worker.js, version.json yangilandi")
PY

# ---------- 3. Atomik yuklash ----------
# `.deploytmp` ga yozib, keyin `mv` — o'quvchi doim BUTUN faylni ko'radi.
echo "== Yuklash =="
upload() {
  local f="$1"
  "${SSH[@]}" "mkdir -p '$ROOT/$(dirname "$f")'"
  scp -q -i "$KEY" "$f" "$HOST:$ROOT/$f.deploytmp"
  "${SSH[@]}" "mv -f '$ROOT/$f.deploytmp' '$ROOT/$f'"
  echo "  yuklandi  $f"
}
for f in "${FILES[@]}"; do upload "$f"; done
# index.html ENG OXIRIDA — yangi `?v=` manzillari faqat fayllar joyiga
# yetgandan keyin e'lon qilinsin, aks holda oradagi lahzada 404 bo'lardi.
upload service-worker.js
upload version.json
upload index.html

# ---------- 4. Serverdan qaytarib tekshirish ----------
echo "== Tasdiqlash =="
fail=0
for f in "${FILES[@]}" service-worker.js version.json index.html; do
  l=$(stat -c%s "$f")
  r=$("${SSH[@]}" "stat -c%s '$ROOT/$f'")
  if [ "$l" = "$r" ]; then echo "  ok  $f ($l bayt)"
  else echo "  HAJM MOS EMAS: $f  mahalliy=$l server=$r"; fail=1; fi
done
[ "$fail" -eq 0 ] || { echo "XATO: yuklash to'liq bo'lmadi."; exit 1; }

# Bir lahzalik tarmoq uzilishi tufayli bekorga "mos kelmadi" demasin —
# bir marta yiqilgani shundan bo'lgan edi, aslida hammasi joyida edi.
srv=""
for i in 1 2 3 4 5; do
  srv=$(curl -s --max-time 10 "https://y.wstore.uz/version.json?t=$(date +%s)$i" | tr -d '{}" ' | sed 's/build://')
  [ "$srv" = "$BUILD" ] && break
  sleep 2
done
echo "  serverdagi build: ${srv:-javobsiz}"
[ "$srv" = "$BUILD" ] || { echo "  OGOHLANTIRISH: version.json mos kelmadi (5 urinishdan keyin)"; exit 1; }

echo
echo "Tayyor. Build: $BUILD"
