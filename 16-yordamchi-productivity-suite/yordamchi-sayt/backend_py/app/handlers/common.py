"""Handler'lar uchun umumiy yordamchilar."""

from __future__ import annotations

import re
from typing import Any


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def s(value: Any) -> str:
    return "" if value is None else str(value).strip()


# --- Quiz baza nomlari (PHP app_normalize_quiz_segment / parse_quiz_full_name) ---

def normalize_quiz_segment(value: Any) -> str:
    v = "" if value is None else str(value).strip()
    v = re.sub(r"\s+", "_", v)
    v = re.sub(r"_+", "_", v)
    return v.strip("_")


def parse_quiz_full_name(value: Any) -> dict[str, str]:
    v = "" if value is None else str(value).strip()
    parts = v.split("__", 1)
    if len(parts) == 2:
        subject = normalize_quiz_segment(parts[0])
        base = normalize_quiz_segment(parts[1])
    else:
        subject = "Boshqa"
        base = normalize_quiz_segment(v)

    if subject == "":
        subject = "Boshqa"
    if base == "":
        base = "Asosiy"

    return {"subject": subject, "base": base, "full": f"{subject}__{base}"}
