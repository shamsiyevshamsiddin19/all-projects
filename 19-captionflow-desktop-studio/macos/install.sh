#!/usr/bin/env bash
# Subtitr Desktop — macOS o'rnatuvchi (administrator huquqi shart emas).
# Dasturni ~/Applications/SubtitrDesktop ga ko'chiradi.
#
# DIQQAT: Mac'da sinalmagan.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${SUBTITR_PREFIX:-$HOME/Applications/SubtitrDesktop}"

say() { printf '\033[1;36m==> %s\033[0m\n' "$*"; }

APP="$(find "$SRC" -maxdepth 1 -name '*.app' | head -1)"
[ -n "$APP" ] || { echo "XATO: .app topilmadi ($SRC)" >&2; exit 1; }

if [ "$SRC" != "$TARGET" ]; then
  say "Fayllar ko'chirilmoqda -> $TARGET"
  mkdir -p "$(dirname "$TARGET")"
  [ -f "$TARGET/.env" ] && cp "$TARGET/.env" "$TMPDIR/.subtitr-env.bak"
  rm -rf "$TARGET"
  mkdir -p "$TARGET"
  cp -a "$SRC/." "$TARGET/"
  [ -f "$TMPDIR/.subtitr-env.bak" ] && mv "$TMPDIR/.subtitr-env.bak" "$TARGET/.env"
fi

# Internetdan yuklangan fayllarga macOS "karantin" belgisini qo'yadi va
# imzolanmagan ilovani ochishdan bosh tortadi. Belgini olib tashlaymiz.
say "Karantin belgisi olib tashlanmoqda"
xattr -dr com.apple.quarantine "$TARGET" 2>/dev/null || true

if ! command -v ffmpeg >/dev/null; then
  printf '\033[1;33mDIQQAT:\033[0m ffmpeg topilmadi. O'"'"'rnating: brew install ffmpeg\n'
fi

TARGET_APP="$(find "$TARGET" -maxdepth 1 -name '*.app' | head -1)"
printf '\n\033[1;32mO'"'"'rnatildi:\033[0m %s\n' "$TARGET"
printf 'Ishga tushirish: open "%s"\n' "$TARGET_APP"
printf 'O'"'"'chirish:       rm -rf "%s"\n' "$TARGET"
