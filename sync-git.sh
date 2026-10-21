#!/usr/bin/env bash
set -e

# Loyihalar papkasidagi Git avtomatik sinxronizatsiya va GitHub activity oshirish skripti
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
if [ $# -gt 0 ]; then
    python3 "$DIR/sync-git.py" "$@"
else
    python3 "$DIR/sync-git.py" "feat: update projects and enhance codebase"
fi
