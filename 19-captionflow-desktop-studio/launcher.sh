#!/usr/bin/env bash
# Subtitr Desktop ishga tushirgichi.
#
# O'rnatilgan ilova manba (.py) ko'rinishida ishlaydi, shuning uchun natijalar
# sukut bo'yicha ilova papkasiga tushardi. Bu skript ularni ko'rinadigan
# Videolar papkasiga, ishchi/model fayllarni esa keshga yo'naltiradi.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VIDEOS="$(xdg-user-dir VIDEOS 2>/dev/null || true)"
[ -n "${VIDEOS:-}" ] || VIDEOS="$HOME/Videos"

export SUBTITR_KINO_DIR="${SUBTITR_KINO_DIR:-$VIDEOS}"
export SUBTITR_OUT_DIR="${SUBTITR_OUT_DIR:-$VIDEOS/Subtitr natijalar}"
export SUBTITR_DATA_DIR="${SUBTITR_DATA_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/SubtitrDesktop}"

exec "$HERE/subtitr_app" "$@"
