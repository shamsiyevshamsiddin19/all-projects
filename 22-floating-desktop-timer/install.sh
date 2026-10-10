#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Suzuvchi Taymer (Floating Timer) o'rnatilmoqda..."

chmod +x "$DIR/main.py"
chmod +x "$DIR/run.sh"

# 1. ~/.local/bin ga buyruq qo'shish
mkdir -p "$HOME/.local/bin"
ln -sf "$DIR/run.sh" "$HOME/.local/bin/floating-timer"

# 2. Desktop launcher qo'shish
mkdir -p "$HOME/.local/share/applications"
cp "$DIR/floating-timer.desktop" "$HOME/.local/share/applications/floating-timer.desktop"
chmod +x "$HOME/.local/share/applications/floating-timer.desktop"

# 3. Desktop ma'lumotlar bazasini yangilash
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo "✅ O'rnatish yakunlandi!"
echo "👉 Terminal orqali ishga tushirish: floating-timer"
echo "👉 Yoki Ubuntu ilovalar menyusidan 'Suzuvchi Taymer' deb qidiring."
