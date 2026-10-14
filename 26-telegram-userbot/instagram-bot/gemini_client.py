"""Gemini bilan aqlli javob yaratish (REST API — sinovdan o'tgan, ishonchli)."""
import requests

import config

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)


def generate_reply(user_message: str, context: str = "") -> str:
    """
    Foydalanuvchi xabariga Gemini yordamida javob yaratadi.

    user_message: kelgan xabar / izoh matni
    context: qo'shimcha kontekst (masalan: "Bu post izohiga javob")
    """
    prompt_parts = [config.BOT_PERSONA]
    if context:
        prompt_parts.append(f"Kontekst: {context}")
    prompt_parts.append(
        f"Foydalanuvchi shunday yozdi: \"{user_message}\"\n"
        f"Unga tabiiy, samimiy va foydali javob yoz. "
        f"Javob {config.MAX_REPLY_CHARS} belgidan oshmasin. "
        f"Faqat javob matnini yoz, boshqa hech narsa qo'shma."
    )
    prompt = "\n\n".join(prompt_parts)

    url = GEMINI_URL.format(model=config.GEMINI_MODEL)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 800,
            # gemini-flash (3.x) "thinking" modeli — ichki o'ylashni o'chiramiz,
            # aks holda o'ylash tokenlari javobni kesib qo'yadi
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    params = {"key": config.GEMINI_API_KEY}

    try:
        r = requests.post(url, json=payload, params=params, timeout=30)
        if r.status_code >= 400:
            print(f"[Gemini xato] {r.status_code}: {r.text[:300]}")
            return _fallback()

        data = r.json()
        text = _extract_text(data)
        if not text:
            return _fallback()
        return text[: config.MAX_REPLY_CHARS]
    except Exception as e:
        print(f"[Gemini istisno] {e}")
        return _fallback()


def _extract_text(data: dict) -> str:
    """Gemini javobidan matnni ajratib oladi."""
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [p.get("text", "") for p in parts if p.get("text")]
        return " ".join(texts).strip()
    except Exception:
        return ""


def _fallback() -> str:
    """Gemini ishlamay qolsa ham bot to'xtamasligi uchun zaxira javob."""
    return "Rahmat xabaringiz uchun! Tez orada javob beraman 🙌"
