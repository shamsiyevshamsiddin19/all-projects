#!/usr/bin/env bash
# Subtitr Desktop — Linux release yig'uvchi.
#
# Chiqish: dist/SubtitrDesktop/ — Flutter GUI, Python protsessor, uning virtual
# muhiti va yt-dlp bir papkada. `install.sh` shu papkani foydalanuvchi uchun
# o'rnatadi. Windows varianti uchun build_release.ps1 ga qarang.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/subtitr_app"
DIST="$ROOT/dist/SubtitrDesktop"
BUNDLE="$APP_DIR/build/linux/x64/release/bundle"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

command -v flutter >/dev/null || die "flutter topilmadi (PATH ga qo'shing)"
command -v python3 >/dev/null || die "python3 topilmadi"

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
if [ ! -x "$ROOT/tools/yt-dlp" ]; then
  curl -fL --retry 3 -o "$ROOT/tools/yt-dlp" \
    https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux
  chmod +x "$ROOT/tools/yt-dlp"
fi

say "4/5 dist/ yig'ilmoqda"
rm -rf "$DIST"
mkdir -p "$DIST"
cp -a "$BUNDLE/." "$DIST/"
cp "$ROOT/desktop_processor.py" "$DIST/"
cp "$ROOT/desktop_requirements.txt" "$DIST/"
cp "$ROOT/.env.example" "$DIST/"
[ -f "$ROOT/ISHLATISH_LINUX.txt" ] && cp "$ROOT/ISHLATISH_LINUX.txt" "$DIST/"
cp "$APP_DIR/assets/app_logo.png" "$DIST/"
mkdir -p "$DIST/tools"
cp "$ROOT/tools/yt-dlp" "$DIST/tools/"
# Virtual muhit ko'chirilganda ham ishlaydi: interpretator yonidagi
# pyvenv.cfg orqali o'z site-packages'ini topadi (`python -m pip` bilan
# chaqiramiz, shuning uchun eski shebang'lar muammo qilmaydi).
cp -a "$ROOT/.venv" "$DIST/.venv"
cp "$ROOT/install.sh" "$DIST/install.sh"
cp "$ROOT/launcher.sh" "$DIST/subtitr-desktop"
chmod +x "$DIST/install.sh" "$DIST/subtitr-desktop" "$DIST/subtitr_app" "$DIST/tools/yt-dlp"

say "5/5 Arxiv"
(cd "$ROOT/dist" && tar czf SubtitrDesktop-linux-x64.tar.gz SubtitrDesktop)

printf '\n\033[1;32mTayyor:\033[0m %s\n' "$DIST"
printf '        %s (%s)\n' "$ROOT/dist/SubtitrDesktop-linux-x64.tar.gz" \
  "$(du -h "$ROOT/dist/SubtitrDesktop-linux-x64.tar.gz" | cut -f1)"
printf '\nO'"'"'rnatish:  %s\n' "$DIST/install.sh"
