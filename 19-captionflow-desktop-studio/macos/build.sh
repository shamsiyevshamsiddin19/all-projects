#!/usr/bin/env bash
# Subtitr Desktop — macOS release yig'uvchi.
#
# Chiqish: dist/SubtitrDesktop/ — ilova bundle'i (.app), Python protsessor,
# uning virtual muhiti va yt-dlp bir papkada. Ilova protsessorni O'Z
# papkasidan yuqoriga qarab qidiradi, shuning uchun .app va qolgan fayllar
# bitta papkada turishi kerak.
#
# DIQQAT: bu skript Mac'da sinalmagan (muallifda Mac yo'q). Linux variantidan
# ko'chirilgan va macOS farqlariga moslangan. Muammo chiqsa — xabar bering.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/subtitr_app"
DIST="$ROOT/dist/SubtitrDesktop"
BUILD="$APP_DIR/build/macos/Build/Products/Release"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(uname)" = "Darwin" ] || die "bu skript faqat macOS uchun"
command -v flutter >/dev/null || die "flutter topilmadi (PATH ga qo'shing)"
command -v python3 >/dev/null || die "python3 topilmadi"

say "1/5 Flutter macOS release yig'ilmoqda"
(cd "$APP_DIR" && flutter pub get && flutter build macos --release)
APP="$(find "$BUILD" -maxdepth 1 -name '*.app' | head -1)"
[ -n "$APP" ] || die "bundle topilmadi: $BUILD"

say "2/5 Python virtual muhiti tayyorlanmoqda"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv" || die "venv yaratilmadi"
fi
"$ROOT/.venv/bin/python" -m pip install --upgrade -q pip
"$ROOT/.venv/bin/python" -m pip install -q -r "$ROOT/desktop_requirements.txt"

say "3/5 yt-dlp tekshirilmoqda"
mkdir -p "$ROOT/tools"
if [ ! -x "$ROOT/tools/yt-dlp" ]; then
  curl -fL --retry 3 -o "$ROOT/tools/yt-dlp" \
    https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
  chmod +x "$ROOT/tools/yt-dlp"
fi

say "4/5 dist/ yig'ilmoqda"
rm -rf "$DIST"
mkdir -p "$DIST"
cp -a "$APP" "$DIST/"
cp "$ROOT/desktop_processor.py" "$DIST/"
rm -rf "$DIST/subtitr"
cp -a "$ROOT/subtitr" "$DIST/subtitr"
find "$DIST/subtitr" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
cp "$ROOT/desktop_requirements.txt" "$DIST/"
cp "$ROOT/.env.example" "$DIST/"
cp "$ROOT/macos/install.sh" "$DIST/install.sh"
mkdir -p "$DIST/tools"
cp "$ROOT/tools/yt-dlp" "$DIST/tools/"
if compgen -G "$ROOT/fonts/*.ttf" >/dev/null; then
  mkdir -p "$DIST/fonts"
  cp "$ROOT"/fonts/*.ttf "$DIST/fonts/"
fi
cp -a "$ROOT/.venv" "$DIST/.venv"
chmod +x "$DIST/install.sh" "$DIST/tools/yt-dlp"

say "5/5 Arxiv"
ARCH="$(uname -m)"   # arm64 (Apple Silicon) yoki x86_64 (Intel)
tar -czf "$ROOT/dist/SubtitrDesktop-macos-$ARCH.tar.gz" -C "$ROOT/dist" SubtitrDesktop

printf '\n\033[1;32mTayyor:\033[0m %s\n' "$DIST"
printf '        %s\n' "$ROOT/dist/SubtitrDesktop-macos-$ARCH.tar.gz"
printf '\nO'"'"'rnatish:  %s\n' "$DIST/install.sh"
