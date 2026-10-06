"""AI JSON javoblarini mustahkam o'qish.

AI ba'zan JSON'ni markdown ichida, izoh bilan yoki KESILGAN holda qaytaradi
(max_tokens chegarasi). Bu modul to'liq massivni o'qishga urinadi; bo'lmasa,
matndan TUGAL obyektlarni bittalab ajratib oladi — kesilgan oxirgi obyekt
tashlab yuboriladi, qolganlari saqlanadi.
"""
from __future__ import annotations
import json
import re


def parse_json_objects(text: str) -> list[dict]:
    """Matndan dict obyektlar ro'yxatini oladi (buzuq/kesilgan JSONga chidamli)."""
    if not text:
        return []
    # 1) Markdown fence ichini ochamiz
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1)

    # 2) To'liq massivni o'qishga urinish
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict)]
        except (ValueError, TypeError):
            pass

    # 3) Balanslangan {} obyektlarni bittalab ajratish (kesilgan JSON uchun)
    objs: list[dict] = []
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        if isinstance(obj, dict):
                            objs.append(obj)
                    except (ValueError, TypeError):
                        pass
                    start = -1
    return objs
