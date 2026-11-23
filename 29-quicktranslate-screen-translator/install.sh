#!/usr/bin/env bash
# Quick Translate kengaytmasini o'rnatadi.
#
# Mavjud o'rnatma ustiga yozadi, lekin ~/.config/quick-translate/ dagi
# API kalitlarga va ~/.local/share/quick-translate/ dagi lug'atga tegmaydi.

set -euo pipefail

UUID="quick-translate@shamsiddin"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.local/share/gnome-shell/extensions/$UUID"

echo "==> Talablarni tekshirish"
missing=()
command -v tesseract >/dev/null || missing+=("tesseract-ocr")
command -v wl-paste   >/dev/null || missing+=("wl-clipboard")
command -v glib-compile-schemas >/dev/null || missing+=("libglib2.0-dev-bin")

if [ ${#missing[@]} -gt 0 ]; then
    echo "    YO'Q: ${missing[*]}"
    echo "    sudo apt install ${missing[*]} tesseract-ocr-rus tesseract-ocr-eng"
    exit 1
fi

langs="$(tesseract --list-langs 2>/dev/null | tail -n +2 | tr '\n' ' ')"
echo "    tesseract $(tesseract --version 2>&1 | head -1 | awk '{print $2}') — tillar: ${langs}"

echo "==> Nusxalash: $TARGET"
mkdir -p "$TARGET"
rsync -a --delete \
    --exclude='.git' \
    --exclude='install.sh' \
    --exclude='README.md' \
    "$SOURCE/" "$TARGET/"

echo "==> Schema kompilyatsiyasi"
glib-compile-schemas "$TARGET/schemas/"

echo "==> Kengaytmani yoqish"
# Wayland'da ishlayotgan Shell yangi kengaytmani ko'rmaydi, shuning uchun
# gnome-extensions CLI o'rniga gsettings ro'yxati to'g'ridan-to'g'ri tahrirlanadi.
current="$(gsettings get org.gnome.shell enabled-extensions)"
if [[ "$current" != *"$UUID"* ]]; then
    if [[ "$current" == "@as []" ]]; then
        gsettings set org.gnome.shell enabled-extensions "['$UUID']"
    else
        gsettings set org.gnome.shell enabled-extensions "${current%]*}, '$UUID']"
    fi
    echo "    ro'yxatga qo'shildi"
else
    echo "    allaqachon ro'yxatda"
fi

cat <<'EOF'

==> Tayyor.

MUHIM: tizimdan chiqib qaytib kiring (logout -> login).
Wayland'da GNOME Shell'ni qayta ishga tushirmasdan kengaytma kodi
yuklanmaydi: Alt+F2 r Wayland'da yo'q, disable/enable esa ES modulini
registridan qayta o'qimaydi.

Keyin:
  Ctrl+Alt+Z  — belgilangan matnni tarjima qilish
  Ctrl+Alt+X  — ekranni qotirib rasmdagi matnni belgilash

Diagnostika:
  journalctl --user -f -o cat | grep -i quicktranslate
EOF
