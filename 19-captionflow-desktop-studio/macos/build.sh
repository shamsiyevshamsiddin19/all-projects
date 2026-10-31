#!/usr/bin/env bash
# Subtitr Desktop — macOS release yig'uvchi.
#
# Chiqish: `dist/SubtitrDesktop-<versiya>-macos-<arch>.dmg`.
#
# Python protsessor, uning virtual muhiti va yt-dlp `.app/Contents/Resources`
# ichiga joylanadi. Shu sababli foydalanuvchi faqat bitta `.app` ni ko'chirsa
# ham dastur ishlaydi; tashqarida qolgan, tasodifan o'chib ketadigan yon
# fayllarga tayanmaydi.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/subtitr_app"
BUILD="$APP_DIR/build/macos/Build/Products/Release"
DIST="$ROOT/dist"
VERSION="$(sed -nE 's/^version:[[:space:]]*([^+[:space:]]+).*/\1/p' "$APP_DIR/pubspec.yaml" | head -n1)"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(uname)" = "Darwin" ] || die "bu skript faqat macOS uchun"
command -v flutter >/dev/null || die "flutter topilmadi (PATH ga qo'shing)"
command -v python3 >/dev/null || die "python3 topilmadi"
command -v hdiutil >/dev/null || die "hdiutil topilmadi (macOS tizim vositasi kerak)"
[ -n "$VERSION" ] || die "subtitr_app/pubspec.yaml dan versiya o'qilmadi"

verify_sha256() {
  local target="$1"
  local expected="$2"
  [ -f "$target" ] || return 1
  printf '%s  %s\n' "$expected" "$target" | shasum -a 256 -c - >/dev/null
}

say "1/7 Flutter macOS release yig'ilmoqda"
(cd "$APP_DIR" && flutter pub get && flutter build macos --release)
APP="$(find "$BUILD" -maxdepth 1 -name '*.app' | head -1)"
[ -n "$APP" ] || die "bundle topilmadi: $BUILD"

say "2/7 Python va PyInstaller tayyorlanmoqda"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv" || die "venv yaratilmadi"
fi
"$ROOT/.venv/bin/python" -m pip install --upgrade -q pip
"$ROOT/.venv/bin/python" -m pip install -q -r "$ROOT/desktop_requirements.txt" pyinstaller

say "3/7 yt-dlp tekshirilmoqda"
mkdir -p "$ROOT/tools"
YTDLP_BIN="$ROOT/tools/yt-dlp"
# `latest` o'zgaruvchan: har bir release aynan tekshirilgan binarni olishi
# uchun versiya va SHA256 qotiriladi.
YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/yt-dlp_macos"
YTDLP_SHA256="0f922c15ccc0b83eefa1c8bc9104e434318c4bf16e408e1ee93b7745a6efe0aa"
if [ -f "$YTDLP_BIN" ] && ! verify_sha256 "$YTDLP_BIN" "$YTDLP_SHA256"; then
  rm -f "$YTDLP_BIN"
fi
if [ ! -f "$YTDLP_BIN" ]; then
  TMP_YTDLP="$YTDLP_BIN.tmp.$$"
  curl -fL --connect-timeout 15 --max-time 180 --retry 3 --retry-delay 2 \
    -o "$TMP_YTDLP" "$YTDLP_URL"
  if ! verify_sha256 "$TMP_YTDLP" "$YTDLP_SHA256"; then
    rm -f "$TMP_YTDLP"
    die "yt-dlp SHA256 nazorat summasi mos kelmadi"
  fi
  mv "$TMP_YTDLP" "$YTDLP_BIN"
  chmod +x "$ROOT/tools/yt-dlp"
fi

ARCH="$(uname -m)"   # arm64 (Apple Silicon) yoki x86_64 (Intel)
RELEASE_NAME="SubtitrDesktop-${VERSION}-macos-${ARCH}"
STAGE="$DIST/$RELEASE_NAME"
RUNTIME="$APP/Contents/Resources/SubtitrRuntime"
PYINSTALLER_DIST="$ROOT/build/pyinstaller-macos/dist"
PYINSTALLER_WORK="$ROOT/build/pyinstaller-macos/work"
PYINSTALLER_SPEC="$ROOT/build/pyinstaller-macos/spec"

say "4/7 Python protsessorni mustaqil binarga yig'ish"
# macOS'ning yangi versiyalarida `python3` oldindan o'rnatilgan bo'lishi
# shart emas. Windows release bilan bir xil, cloud-first PyInstaller spec
# ishlatiladi: foydalanuvchiga Python/venv berkitilmaydi.
rm -rf "$PYINSTALLER_DIST" "$PYINSTALLER_WORK" "$PYINSTALLER_SPEC"
(cd "$ROOT" && "$ROOT/.venv/bin/python" -m PyInstaller --clean --noconfirm \
  --distpath "$PYINSTALLER_DIST" --workpath "$PYINSTALLER_WORK" \
  --specpath "$PYINSTALLER_SPEC" windows/desktop_processor.spec)
[ -x "$PYINSTALLER_DIST/desktop_processor" ] \
  || die "PyInstaller desktop_processor binarini yaratmadi"

say "5/7 .app ichiga protsessor joylanmoqda"
# Flutter build katalogi har safar qayta yaratiladi. Runtime'ni aynan yakuniy
# .app ichiga qo'yish macOS paketining mustaqilligini kafolatlaydi.
rm -rf "$RUNTIME" "$STAGE"
mkdir -p "$RUNTIME" "$STAGE"
cp "$PYINSTALLER_DIST/desktop_processor" "$RUNTIME/"
cp "$ROOT/.env.example" "$RUNTIME/"
mkdir -p "$RUNTIME/tools"
cp "$YTDLP_BIN" "$RUNTIME/tools/yt-dlp"
if compgen -G "$ROOT/fonts/*.ttf" >/dev/null; then
  mkdir -p "$RUNTIME/fonts"
  cp "$ROOT"/fonts/*.ttf "$RUNTIME/fonts/"
fi
chmod +x "$RUNTIME/tools/yt-dlp"

# Dastur ichida Runtime topilgani haqiqiy paketning ishlash sharti.
[ -x "$RUNTIME/desktop_processor" ] || die "runtime protsessor nusxalanmadi"

# Runtime `.app`ga Flutter buildidan keyin qo'shildi, shu bois yakuniy bundle
# qayta imzolanadi. Sertifikat bo'lmasa `-` ad-hoc imzosi Gatekeeper uchun
# foydalanuvchining "Open" tasdig'ini saqlaydi; sertifikat bo'lsa u bilan
# haqiqiy Developer ID imzosi qo'yiladi.
SIGN_IDENTITY="${SUBTITR_MACOS_SIGN_IDENTITY:--}"
codesign --force --deep --sign "$SIGN_IDENTITY" --timestamp=none "$APP"
codesign --verify --deep --strict "$APP"

say "6/7 DMG uchun staging"
cp -a "$APP" "$STAGE/"
cp "$ROOT/macos/install.sh" "$STAGE/install.sh"
cp "$ROOT/macos/README.md" "$STAGE/README-macOS.md"
chmod +x "$STAGE/install.sh"

say "7/7 DMG va SHA256"
DMG="$DIST/$RELEASE_NAME.dmg"
CHECKSUM="$DIST/$RELEASE_NAME.dmg.sha256"
rm -f "$DMG" "$CHECKSUM"
hdiutil create -volname "Subtitr Desktop" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
(cd "$DIST" && shasum -a 256 "$(basename "$DMG")" > "$(basename "$CHECKSUM")")
(cd "$DIST" && shasum -a 256 -c "$(basename "$CHECKSUM")" >/dev/null)

printf '\n\033[1;32mTayyor:\033[0m %s\n' "$DMG"
printf '        SHA256: %s\n' "$CHECKSUM"
printf '\nDMG ichida: %s/*.app va install.sh\n' "$RELEASE_NAME"
