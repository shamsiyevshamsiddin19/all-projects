"""Har bir akkaunt uchun sozlamalarni diskda saqlaydi (restartda yo'qolmaydi).

Fayl: data/state_<akkaunt>.json
"""
import json
import os

import config

_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
_PATH = os.path.join(_DIR, f"state_{config.SESSION}.json")


def load() -> dict:
    try:
        with open(_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 — fayl yo'q yoki buzuq
        return {}


def save(data: dict) -> None:
    os.makedirs(_DIR, exist_ok=True)
    tmp = _PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _PATH)  # atomik yozish


def get(key, default=None):
    return load().get(key, default)


def set(key, value) -> None:
    data = load()
    data[key] = value
    save(data)
