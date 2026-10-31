#!/usr/bin/env bash
# Subtitr Desktop — Linux release yig'uvchi.
#
# Chiqish: dist/SubtitrDesktop/ — Flutter GUI, Python protsessor, uning virtual
# muhiti va yt-dlp bir papkada. `install.sh` shu papkani foydalanuvchi uchun
# o'rnatadi. Windows varianti uchun build_release.ps1 ga qarang.
set -euo pipefail

# Skript `linux/` ichida — loyiha ildizi bitta yuqorida.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/subtitr_app"
DIST="$ROOT/dist/SubtitrDesktop"
BUNDLE="$APP_DIR/build/linux/x64/release/bundle"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

# SHA256 xesh tekshiruvi.
# Nima uchun: tashqi manbadan yuklab olinayotgan binar va shrift fayllarining
# yaxlitligini (integrity) va xavfsizligini kafolatlash uchun. Tarmoqdagi uzilishlar,
# chala yuklanishlar yoki fayl buzilishlarining oldi olinadi.
verify_sha256() {
  local target="$1"
  local expected="$2"
  [ -f "$target" ] || return 1
  printf '%s  %s\n' "$expected" "$target" | sha256sum -c --status 2>/dev/null
}

command -v flutter >/dev/null || die "flutter topilmadi (PATH ga qo'shing)"
command -v python3 >/dev/null || die "python3 topilmadi"
# Tahrirlash oynasidagi pleyer (media_kit) Linux'da TIZIMDAGI libmpv ni
# ishlatadi va u build vaqtida pkg-config orqali talab qilinadi. Usiz
# `flutter build linux` tushunarsiz CMake xatosi bilan to'xtaydi.
pkg-config --exists mpv 2>/dev/null \
  || die "libmpv topilmadi — 'sudo apt install libmpv-dev mpv' bajaring"

say "1/5 Flutter Linux release yig'ilmoqda"
(cd "$APP_DIR" && flutter pub get && flutter build linux --release)
[ -x "$BUNDLE/subtitr_app" ] || die "bundle topilmadi: $BUNDLE"

say "2/5 Python virtual muhiti tayyorlanmoqda"
# PEP 668 (Ubuntu 23.04+) tizim Python'iga o'rnatishni bloklaydi — paketlar
# har doim dastur yonidagi .venv ichida yashaydi.
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv" \
    || die "venv yaratilmadi — 'sudo apt install python3-venv' kerak bo'lishi mumkin"
fi
"$ROOT/.venv/bin/python" -m pip install --upgrade -q pip
"$ROOT/.venv/bin/python" -m pip install -q -r "$ROOT/desktop_requirements.txt"

say "3/5 yt-dlp tekshirilmoqda"
mkdir -p "$ROOT/tools"
YTDLP_BIN="$ROOT/tools/yt-dlp"
# Versiya qat'iy belgilangan: latest doim o'zgaradi va SHA256 nazorat summasini buzadi.
# Shu sababli aniq barqaror versiya va uning rasmiy SHA256 xeshi ko'rsatiladi.
YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/yt-dlp_linux"
YTDLP_SHA256="767ba9dce7052aa196f8b12652f433d76de128ba168966fa84b6394d5e6c6795"

if [ -f "$YTDLP_BIN" ]; then
  # Agar fayl avval yuklangan bo'lsa, yaxlitligini xesh orqali tekshiramiz.
  if verify_sha256 "$YTDLP_BIN" "$YTDLP_SHA256"; then
    chmod +x "$YTDLP_BIN"
  else
    say "Ogohlantirish: Mavjud yt-dlp nazorat summasi (SHA256) mos kelmadi, qayta yuklanadi..."
    rm -f "$YTDLP_BIN"
  fi
fi

if [ ! -f "$YTDLP_BIN" ]; then
  say "yt-dlp yuklab olinmoqda ($YTDLP_URL)..."
  # Vaqtinchalik faylga yuklaymiz — agar tarmoq uzilsa chala fayl tools/ papkasida qolib ketmaydi.
  TMP_YTDLP="$YTDLP_BIN.tmp.$$"
  if ! curl -fL --connect-timeout 15 --max-time 180 --retry 3 --retry-delay 2 -o "$TMP_YTDLP" "$YTDLP_URL"; then
    rm -f "$TMP_YTDLP"
    die "Internetga ulanib bo'lmadi yoki tarmoq xatosi yuz berdi: yt-dlp yuklanmadi. Internet aloqasini tekshiring."
  fi

  # Yaxlitlikni tekshiramiz
  if ! verify_sha256 "$TMP_YTDLP" "$YTDLP_SHA256"; then
    rm -f "$TMP_YTDLP"
    die "yt-dlp faylining SHA256 nazorat summasi mos kelmadi! Fayl to'liq yuklanmagan yoki shikastlangan bo'lishi mumkin."
  fi

  mv "$TMP_YTDLP" "$YTDLP_BIN"
  chmod +x "$YTDLP_BIN"
fi

say "3.5/5 Subtitr shrifti tekshirilmoqda"
# Tizimdagi Noto Sans faqat Bold (700) gacha — kuydirilgan subtitr kuchsiz
# ko'rinadi. Montserrat Black (OFL, kirill + o'zbek harflari bor) qo'shiladi.
mkdir -p "$ROOT/fonts"
FONT_FILE="$ROOT/fonts/Montserrat-Black.ttf"
# Montserrat rasmiy mualliflik (Julieta Ulanovsky) repozitoriyasidan olinadi
FONT_URL="https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf"
FONT_SHA256="ea67b37f8776eebea135cd1fe9adeaf6f9427683e8dc11ab8398b6be5f102c60"

if [ -f "$FONT_FILE" ]; then
  # Agar shrift fayli mavjud bo'lsa, xeshini tekshiramiz.
  if ! verify_sha256 "$FONT_FILE" "$FONT_SHA256"; then
    say "Ogohlantirish: Mavjud Montserrat-Black.ttf nazorat summasi mos kelmadi, qayta yuklanadi..."
    rm -f "$FONT_FILE"
  fi
fi

if [ ! -f "$FONT_FILE" ]; then
  say "Montserrat-Black.ttf shrifti yuklab olinmoqda..."
  TMP_FONT="$FONT_FILE.tmp.$$"
  if curl -fsSL --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 2 -o "$TMP_FONT" "$FONT_URL"; then
    if verify_sha256 "$TMP_FONT" "$FONT_SHA256"; then
      mv "$TMP_FONT" "$FONT_FILE"
    else
      rm -f "$TMP_FONT"
      say "Ogohlantirish: Yuklangan shriftning SHA256 summasi mos kelmadi — Noto Sans bilan ishlaydi."
    fi
  else
    rm -f "$TMP_FONT"
    say "Ogohlantirish: Tarmoq yo'qligi sababli shrift yuklanmadi — tizimdagi Noto Sans ishlatiladi."
  fi
fi

# "O'qish uchun matn" rejimining PDF'i uchun kirill harflari bor serif shrift
# kerak. Yuklab olinmaydi: tizimda doim bittasi topiladi (Linux — Noto Serif /
# DejaVu Serif / Liberation Serif, Windows — Georgia / Times New Roman,
# macOS — Georgia). Boshqa shrift xohlansa, TTF fayllarini `fonts/` ga
# qo'yish kifoya — dastur avval o'sha papkaga qaraydi.

say "4/5 dist/ yig'ilmoqda"
rm -rf "$DIST"
mkdir -p "$DIST"
cp -a "$BUNDLE/." "$DIST/"
cp "$ROOT/desktop_processor.py" "$DIST/"
# Kodning o'zi `subtitr/` paketida — kirish nuqtasi faqat uni chaqiradi.
rm -rf "$DIST/subtitr"
cp -a "$ROOT/subtitr" "$DIST/subtitr"
find "$DIST/subtitr" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
cp "$ROOT/desktop_requirements.txt" "$DIST/"
cp "$ROOT/.env.example" "$DIST/"
[ -f "$ROOT/ISHLATISH_LINUX.txt" ] && cp "$ROOT/ISHLATISH_LINUX.txt" "$DIST/"
cp "$APP_DIR/assets/app_logo.png" "$DIST/"
mkdir -p "$DIST/tools"
cp "$ROOT/tools/yt-dlp" "$DIST/tools/"
if compgen -G "$ROOT/fonts/*.ttf" >/dev/null; then
  mkdir -p "$DIST/fonts"
  cp "$ROOT"/fonts/*.ttf "$DIST/fonts/"
fi
# Virtual muhit ko'chirilganda ham ishlaydi: interpretator yonidagi
# pyvenv.cfg orqali o'z site-packages'ini topadi (`python -m pip` bilan
# chaqiramiz, shuning uchun eski shebang'lar muammo qilmaydi).
cp -a "$ROOT/.venv" "$DIST/.venv"
cp "$ROOT/linux/install.sh" "$DIST/install.sh"
cp "$ROOT/launcher.sh" "$DIST/subtitr-desktop"
chmod +x "$DIST/install.sh" "$DIST/subtitr-desktop" "$DIST/subtitr_app" "$DIST/tools/yt-dlp"

say "5/5 Arxiv"
(cd "$ROOT/dist" && tar czf SubtitrDesktop-linux-x64.tar.gz SubtitrDesktop)
(cd "$ROOT/dist" && sha256sum SubtitrDesktop-linux-x64.tar.gz > SubtitrDesktop-linux-x64.tar.gz.sha256)
(cd "$ROOT/dist" && sha256sum --check SubtitrDesktop-linux-x64.tar.gz.sha256 >/dev/null)

printf '\n\033[1;32mTayyor:\033[0m %s\n' "$DIST"
printf '        %s (%s)\n' "$ROOT/dist/SubtitrDesktop-linux-x64.tar.gz" \
  "$(du -h "$ROOT/dist/SubtitrDesktop-linux-x64.tar.gz" | cut -f1)"
printf '        SHA256: %s\n' "$ROOT/dist/SubtitrDesktop-linux-x64.tar.gz.sha256"
printf '\nO'"'"'rnatish:  %s\n' "$DIST/install.sh"
