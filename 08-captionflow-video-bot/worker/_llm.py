"""LLM JSON kirish/chiqish yordamchilari (correct va translate uchun umumiy).

Pozitsiya o'rniga RAQAMLI KALIT (index) ishlatamiz: model qatorlarni
qo'shib/bo'lib yuborsa ham, har bir qator o'z kaliti bilan joyiga tushadi.
Mos kelmagan kalitlar uchun xom (asl) matn ishlatiladi — xato bermaydi.
"""
from __future__ import annotations

import json


def to_payload(texts: list[str]) -> str:
    """Matnlarni {"0": "...", "1": "..."} JSON ko'rinishiga keltiradi."""
    return json.dumps({str(i): t for i, t in enumerate(texts)}, ensure_ascii=False)


def _strip_fences(content: str) -> str:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`").strip()
        if content[:4].lower() == "json":
            content = content[4:].strip()
    return content


def loads_lenient(content: str) -> dict:
    """JSON o'qiydi; "Extra data" (oxirida ortiqcha) bo'lsa birinchi obyektni oladi."""
    s = _strip_fences(content)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Model JSON dan keyin ortiqcha matn/ikkinchi obyekt qo'shgan bo'lishi mumkin
        obj, _end = json.JSONDecoder().raw_decode(s.lstrip())
        return obj


def from_response(content: str, texts: list[str]) -> tuple[list[str], int]:
    """Javobni kalit bo'yicha moslaydi.

    Qaytaradi: (natija, mos_kelganlar_soni). Natija uzunligi texts bilan
    bir xil — topilmagan kalit uchun asl matn qo'yiladi.
    """
    data = loads_lenient(content)
    if not isinstance(data, dict):
        raise ValueError("JSON obyekt kutilgan edi")

    out: list[str] = []
    matched = 0
    for i, original in enumerate(texts):
        value = data.get(str(i))
        if isinstance(value, (str, int, float)) and str(value).strip():
            out.append(str(value).strip())
            matched += 1
        else:
            out.append(original)
    return out, matched


# ---------------------------------------------------------------- oynali (window) tarjima
# Tarjima sifatini oshirish uchun: har bo'lakka atrofdagi qatorlar "kontekst"
# sifatida beriladi (tarjima qilinmaydi) — olmosh/ohang/davomli gap saqlanadi.

def to_windowed_payload(texts: list[str], start: int, end: int, ctx: int = 6) -> str:
    """range(start,end) ni tarjima uchun, atrofdagi ctx qatorni kontekst qiladi."""
    cb = max(0, start - ctx)
    ca = min(len(texts), end + ctx)
    obj = {
        "context_before": {str(i): texts[i] for i in range(cb, start)},
        "translate": {str(i): texts[i] for i in range(start, end)},
        "context_after": {str(i): texts[i] for i in range(end, ca)},
    }
    return json.dumps(obj, ensure_ascii=False)


def from_windowed_response(
    content: str, texts: list[str], start: int, end: int
) -> tuple[dict[int, str], int]:
    """Oynali javobni o'qiydi — FAQAT range(start,end) kalitlari.

    Model tekis yoki "translate" ichida qaytarsa ham ishlaydi; kontekst
    kalitlari sizib kirsa e'tiborsiz qoldiriladi. Qiymat asl matnga AYNAN
    teng bo'lsa (tarjima qilinmagan) — matched ga QO'SHILMAYDI (fallback
    to'g'ri ishlasin), lekin natijaga baribir qo'yiladi.
    Qaytaradi: ({indeks: matn}, mos_kelgan_tarjimalar_soni).
    """
    data = loads_lenient(content)
    if not isinstance(data, dict):
        raise ValueError("JSON obyekt kutilgan edi")
    block = data.get("translate")
    if not isinstance(block, dict):
        block = data  # model tekis qaytargan

    out: dict[int, str] = {}
    matched = 0
    for i in range(start, end):
        original = texts[i]
        value = block.get(str(i))
        if isinstance(value, (str, int, float)) and str(value).strip():
            text = str(value).strip()
            out[i] = text
            if text != original.strip():  # asl=javob = tarjima qilinmagan
                matched += 1
        else:
            out[i] = original
    return out, matched
