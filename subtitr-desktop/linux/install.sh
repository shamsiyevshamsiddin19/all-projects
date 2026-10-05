#!/usr/bin/env bash
# Subtitr Desktop — Linux o'rnatuvchi (administrator huquqi shart emas).
# Dasturni ~/.local/share/SubtitrDesktop ga ko'chiradi va menyuga yorliq qo'shadi.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${SUBTITR_PREFIX:-$HOME/.local/share/SubtitrDesktop}"
APPS="$HOME/.local/share/applications"
DESKTOP_FILE="$APPS/subtitr-desktop.desktop"

say() { printf '\033[1;36m==> %s\033[0m\n' "$*"; }

[ -x "$SRC/subtitr_app" ] || { echo "XATO: subtitr_app topilmadi ($SRC)" >&2; exit 1; }

if [ "$SRC" != "$TARGET" ]; then
  say "Fayllar ko'chirilmoqda -> $TARGET"
  mkdir -p "$TARGET"
  # Eski nusxani tozalaymiz, lekin foydalanuvchi sozlamalarini (.env) saqlaymiz.
  [ -f "$TARGET/.env" ] && cp "$TARGET/.env" "$TARGET/../.subtitr-env.bak"
  rm -rf "$TARGET"
  mkdir -p "$TARGET"
  cp -a "$SRC/." "$TARGET/"
  [ -f "$TARGET/../.subtitr-env.bak" ] && mv "$TARGET/../.subtitr-env.bak" "$TARGET/.env"
fi
chmod +x "$TARGET/subtitr_app" "$TARGET/subtitr-desktop" "$TARGET/tools/yt-dlp" 2>/dev/null || true

say "Menyu yorlig'i yaratilmoqda"
mkdir -p "$APPS"
cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Subtitr Desktop
Comment=Video subtitr, tarjima va lug'at
Exec=$TARGET/subtitr-desktop
Icon=$TARGET/app_logo.png
Terminal=false
Categories=AudioVideo;Video;
StartupWMClass=com.example.subtitr_app
DESKTOP
chmod +x "$DESKTOP_FILE"

cat > "$TARGET/uninstall.sh" <<UNINST
#!/usr/bin/env bash
# Subtitr Desktop ni o'chirish.
set -e
rm -f "$DESKTOP_FILE"
rm -rf "$TARGET"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
echo "Subtitr Desktop o'chirildi."
UNINST
chmod +x "$TARGET/uninstall.sh"

command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" >/dev/null 2>&1 || true

# ffmpeg dastur ichida kelmaydi — tizimdagisi ishlatiladi.
if ! command -v ffmpeg >/dev/null; then
  printf '\033[1;33mDIQQAT:\033[0m ffmpeg topilmadi. O'"'"'rnating: sudo apt install ffmpeg\n'
fi

printf '\n\033[1;32mO'"'"'rnatildi:\033[0m %s\n' "$TARGET"
printf 'Ishga tushirish: menyudan "Subtitr Desktop" yoki %s\n' "$TARGET/subtitr-desktop"
printf 'O'"'"'chirish:       %s\n' "$TARGET/uninstall.sh"
