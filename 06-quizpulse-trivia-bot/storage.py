"""Testlarni JSON fayl ko'rinishida saqlash."""

import json
import os
import time
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
QUIZ_DIR = os.path.join(BASE, "quizzes")
os.makedirs(QUIZ_DIR, exist_ok=True)


def _path(qid: str) -> str:
    return os.path.join(QUIZ_DIR, qid + ".json")


def save_quiz(name: str, questions: list, owner_id: int) -> str:
    qid = uuid.uuid4().hex[:8]
    data = {
        "id": qid,
        "name": name,
        "owner_id": owner_id,
        "created": int(time.time()),
        "questions": questions,
    }
    with open(_path(qid), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return qid


def load_quiz(qid: str):
    path = _path(qid)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_quizzes():
    out = []
    for fn in os.listdir(QUIZ_DIR):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(QUIZ_DIR, fn), encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
    out.sort(key=lambda d: d.get("created", 0), reverse=True)
    return out


def delete_quiz(qid: str) -> bool:
    path = _path(qid)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
