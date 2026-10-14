"""Gemini AI plugini.

Buyruqlar:
  .ai <savol>        — Gemini'dan javob oladi
  (xabarga javoban) .ai [ko'rsatma]
                     — javob berilgan xabar ustida ishlaydi
                       (masalan: .ai o'zbekchaga tarjima qil)
  .aijavob           — javob berilgan xabarga o'zingiz nomingizdan
                       muloyim javob matnini yozib beradi
"""
import asyncio

import aiohttp

import config

from ._helpers import command, register_all

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


async def ask_gemini(prompt: str, system: str = "") -> str:
    """Gemini API ga so'rov yuboradi va matn javobini qaytaradi."""
    if not config.GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY sozlanmagan. .env fayliga qo'shing."

    url = API_URL.format(model=config.GEMINI_MODEL, key=config.GEMINI_API_KEY)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    last_err = ""
    # Vaqtinchalik xatolarda (tarmoq, 429/5xx) 3 martagacha qayta urinamiz
    for attempt in range(3):
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=body) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        candidates = data.get("candidates", [])
                        if not candidates:
                            return "🤔 Javob bo'sh keldi (ehtimol xavfsizlik filtri)."
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts).strip()
                        return text or "🤔 Javob bo'sh."
                    msg = data.get("error", {}).get("message", str(data))
                    # 429 (limit) yoki 5xx — qayta urinishga arziydi
                    if resp.status == 429 or resp.status >= 500:
                        last_err = f"{resp.status}: {msg}"
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    return f"❌ Xato ({resp.status}): {msg}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            await asyncio.sleep(2 * (attempt + 1))
    return f"❌ Ulanishda xato (qayta urinishlar tugadi): {last_err}"


@command("ai", "Gemini AI'dan javob oladi (.ai savol)")
async def ai_cmd(event):
    query = event.pattern_match.group(1).strip()
    reply = await event.get_reply_message()

    if reply and reply.text:
        # Xabarga javoban ishlatilgan: o'sha xabar matni + ko'rsatma
        instruction = query or "Bu xabarni tushuntir yoki javob ber."
        prompt = f"Ko'rsatma: {instruction}\n\nXabar matni:\n{reply.text}"
    elif query:
        prompt = query
    else:
        await event.edit("Savol yozing: `.ai savolingiz`")
        return

    await event.edit("🧠 O'ylayapman...")
    answer = await ask_gemini(prompt)
    # Telegram xabar chegarasi ~4096 belgi
    await event.edit(answer[:4096])


@command("aijavob", "Javob berilgan xabarga javob matnini yozib beradi")
async def ai_reply(event):
    reply = await event.get_reply_message()
    if not reply or not reply.text:
        await event.edit("Javob yozib berishim uchun bir xabarga javoban yozing.")
        return
    hint = event.pattern_match.group(1).strip()
    system = (
        "Sen foydalanuvchi o'rniga qisqa, tabiiy va muloyim javob matnini "
        "yozib beradigan yordamchisan. Faqat javob matnini yoz, boshqa izoh berma."
    )
    prompt = f"Menga kelgan xabar:\n{reply.text}"
    if hint:
        prompt += f"\n\nQanday javob berishim kerak: {hint}"
    await event.edit("✍️ Javob tayyorlayapman...")
    answer = await ask_gemini(prompt, system=system)
    await event.edit(answer[:4096])


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
