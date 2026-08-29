#!/usr/bin/env bash
# Serverdan oflayn ma'lumot suratini oladi (assets/data/snapshot.json).
#
# Ilova internetsiz ishlashi uchun lug'atlar, .md materiallar va bir nechta
# tayyor javob APK ichiga joylanadi. Bu skript o'shani serverdan yig'adi.
#
# Tayyor javoblar (`canned`) ATAYLAB backendning O'ZIDAN chaqirib olinadi —
# javob shaklini qo'lda takrorlash xatoga olib kelardi.
set -euo pipefail
cd "$(dirname "$0")/.."

KEY="${YORDAMCHI_KEY:-$HOME/.ssh/oracle_yangi}"
HOST="${YORDAMCHI_HOST:-opc@82.70.41.85}"
APP="/opt/yordamchi/Yordamchisayt/backend_py"

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/snap.py" <<'PY'
import json
from starlette.requests import Request
from app import db
from app.handlers import quiz, sport

out = {"dict": {}}
for lang in ("russian", "english"):
    rows = db.fetch_all(
        "SELECT category, word_ru, word_uz, COALESCE(note,'') AS note, "
        "COALESCE(example,'') AS example, COALESCE(pair_with,'') AS pair_with "
        "FROM dictionary_words WHERE lang=:l ORDER BY sort_order, id", {"l": lang})
    order = []
    for r in rows:
        if r["category"] not in order:
            order.append(r["category"])
    out["dict"][lang] = {"items": rows, "order": order}

out["topics"] = db.fetch_all(
    "SELECT id, lang, folder, name, COALESCE(content,'') AS content "
    "FROM language_topics ORDER BY lang, folder, name")

scope = {"type": "http", "method": "POST", "path": "/api", "headers": [],
         "query_string": b"", "session": {"doktor_id": 1, "email": "offline"},
         "client": ("127.0.0.1", 0), "app": None}
req = Request(scope)
def body_of(r): return json.loads(bytes(r.body).decode())

canned = {}
for key, fn in (("get_structure", lambda: quiz.get_structure(req, {})),
                ("global_data",   lambda: quiz.get_data(req, {}, "Global_Data")),
                ("sport_get_all", lambda: sport.get_all(req, {})),
                ("quiz_results",  lambda: quiz.get_quiz_results(req, {}, ""))):
    try:
        canned[key] = body_of(fn())
    except Exception:
        pass
out["canned"] = canned

print(json.dumps(out, ensure_ascii=False, default=str))
PY

scp -q -i "$KEY" "$TMP/snap.py" "$HOST:$APP/snap.py"
mkdir -p assets/data
ssh -i "$KEY" "$HOST" "cd $APP && ./.venv/bin/python snap.py; rm -f snap.py" > assets/data/snapshot.json
echo "Surat olindi: $(du -h assets/data/snapshot.json | cut -f1)"
