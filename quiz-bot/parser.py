"""
Savol fayllarini o'qish (parser).

Ikkala formatni ham qo'llab-quvvatlaydi:

Format A (harfli):
    1. Savol matni
    A) Variant
    B) Variant
    C) Variant
    D) Variant
    Javob: A

Format B (+/- belgili):
    # Savol matni
    + To'g'ri variant
    - Variant
    - Variant
    - Variant

Ikkala formatni bitta faylda aralashtirib ishlatsa ham bo'ladi.
"""

import re

# Savol boshlanishi
_Q_NUM = re.compile(r"^\s*\d+\s*[\.\)]\s*(.*\S)\s*$")        # "1. Savol"  yoki "1) Savol"
_Q_HASH = re.compile(r"^\s*#\s*(.*\S)\s*$")                    # "# Savol"

# Variantlar
_OPT_PM = re.compile(r"^\s*([+\-\*])\s*(.*\S)\s*$")            # "+ variant" / "- variant"
_OPT_LETTER = re.compile(r"^\s*([A-Za-z])\s*[\.\)]\s*(.*\S)\s*$")  # "A) variant" / "A. variant"

# Javob qatori
_ANSWER = re.compile(
    r"^\s*(?:javob|answer|ответ|to\'?g\'?ri\s*javob)\s*[:\-=]\s*(.*\S)\s*$",
    re.IGNORECASE,
)

# Izoh (tushuntirish) qatori
_EXPL = re.compile(
    r"^\s*(?:izoh|tushuntirish|explanation|объяснение)\s*[:\-=]\s*(.*\S)\s*$",
    re.IGNORECASE,
)


def _letter_to_index(token: str):
    """'A' -> 0, 'B' -> 1, '1' -> 0 ..."""
    if not token:
        return None
    ch = token.strip()[0]
    if ch.isdigit():
        return int(ch) - 1
    up = ch.upper()
    if "A" <= up <= "Z":
        return ord(up) - ord("A")
    return None


def parse_quiz(text: str):
    """Matndan savollar ro'yxatini qaytaradi.

    Har bir savol: {"text": str, "options": [str, ...], "correct": int}
    """
    questions = []
    cur = None

    def new_question(qtext):
        return {"text": qtext.strip(), "options": [], "correct": None,
                "answer_token": None, "explanation": None}

    def flush():
        nonlocal cur
        if cur and cur["text"] and len(cur["options"]) >= 2:
            correct = cur["correct"]
            if correct is None and cur["answer_token"] is not None:
                correct = _letter_to_index(cur["answer_token"])
            if correct is None:
                correct = 0
            if correct < 0 or correct >= len(cur["options"]):
                correct = 0
            questions.append(
                {"text": cur["text"], "options": cur["options"], "correct": correct,
                 "explanation": cur.get("explanation")}
            )
        cur = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        # 1) Javob qatori
        m = _ANSWER.match(line)
        if m:
            if cur is not None:
                cur["answer_token"] = m.group(1)
            continue

        # 1b) Izoh qatori
        m = _EXPL.match(line)
        if m:
            if cur is not None:
                cur["explanation"] = m.group(1).strip()
            continue

        # 2) "# Savol" (Format B)
        m = _Q_HASH.match(line)
        if m:
            flush()
            cur = new_question(m.group(1))
            continue

        # 3) "1. Savol" (Format A)
        m = _Q_NUM.match(line)
        if m:
            flush()
            cur = new_question(m.group(1))
            continue

        # 4) "+ / -" variant
        m = _OPT_PM.match(line)
        if m and cur is not None:
            sign, opt = m.group(1), m.group(2).strip()
            if sign == "+":
                cur["correct"] = len(cur["options"])
            cur["options"].append(opt)
            continue

        # 5) "A) variant"
        m = _OPT_LETTER.match(line)
        if m and cur is not None:
            cur["options"].append(m.group(2).strip())
            continue

        # 6) savol matnining davomi (variantlar boshlanmagan bo'lsa)
        if cur is not None and not cur["options"]:
            cur["text"] = (cur["text"] + " " + line.strip()).strip()

    flush()
    return questions


if __name__ == "__main__":
    demo = """
1. Oʻzbekiston poytaxti?
A) Samarqand
B) Toshkent
C) Buxoro
D) Xiva
Javob: B

# 2+2 nechga teng?
- 3
+ 4
- 5
- 22
"""
    for i, q in enumerate(parse_quiz(demo), 1):
        print(i, q)
