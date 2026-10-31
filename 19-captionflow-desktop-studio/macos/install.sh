#!/usr/bin/env bash
# Subtitr Desktop — macOS o'rnatuvchi (administrator huquqi shart emas).
# Dasturni ~/Applications/SubtitrDesktop ga ko'chiradi.
#
# DIQQAT: Mac'da sinalmagan.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$HOME/Applications"
TARGET="${SUBTITR_PREFIX:-$INSTALL_ROOT/SubtitrDesktop}"

say() { printf '\033[1;36m==> %s\033[0m\n' "$*"; }

# O'rnatuvchi faqat ~/Applications ichidagi bola papkani almashtiradi.
# Shu cheklov noto'g'ri SUBTITR_PREFIX bilan HOME kabi katta papkaning
# o'chib ketishini oldini oladi.
INSTALL_ROOT="$(realpath -m "$INSTALL_ROOT")"
TARGET="$(realpath -m "$TARGET")"
case "$TARGET" in
  "$INSTALL_ROOT"/*) ;;
  *)
    echo "XATO: SUBTITR_PREFIX faqat $INSTALL_ROOT ichidagi bola papka bo'lishi kerak." >&2
    exit 1
    ;;
esac

APP="$(find "$SRC" -maxdepth 1 -name '*.app' | head -1)"
[ -n "$APP" ] || { echo "XATO: .app topilmadi ($SRC)" >&2; exit 1; }

if [ "$SRC" != "$TARGET" ]; then
  say "Fayllar ko'chirilmoqda -> $TARGET"
  mkdir -p "$(dirname "$TARGET")"
  BACKUP_DIR="${TMPDIR:-/tmp}"
  [ -f "$TARGET/.env" ] && cp "$TARGET/.env" "$BACKUP_DIR/.subtitr-env.bak"
  rm -rf "$TARGET"
  mkdir -p "$TARGET"
  cp -a "$SRC/." "$TARGET/"
  [ -f "$BACKUP_DIR/.subtitr-env.bak" ] && mv "$BACKUP_DIR/.subtitr-env.bak" "$TARGET/.env"
fi

# Karantin belgisi foydalanuvchining Gatekeeper himoyasidir; uni avtomatik
# olib tashlamaymiz. Notarizatsiyalangan relizda bu muammo bo'lmaydi.

if ! command -v ffmpeg >/dev/null; then
  printf '\033[1;33mDIQQAT:\033[0m ffmpeg topilmadi. O'"'"'rnating: brew install ffmpeg\n'
fi

TARGET_APP="$(find "$TARGET" -maxdepth 1 -name '*.app' | head -1)"
printf '\n\033[1;32mO'"'"'rnatildi:\033[0m %s\n' "$TARGET"
printf 'Ishga tushirish: open "%s"\n' "$TARGET_APP"
printf 'O'"'"'chirish:       rm -rf "%s"\n' "$TARGET"
