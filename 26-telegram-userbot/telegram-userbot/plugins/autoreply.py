"""To'liq avtomatik AI javob rejimi (tasdiqsiz).

Yoqilganda (.autoreply on) shaxsiy xabar yoki guruhdagi mention kelsa,
Gemini o'zi javob yozib, DARHOL yuboradi — .ok kutmaydi.

Himoyalar:
  • O'z akkauntlaringizga javob bermaydi (config.OWN_ACCOUNT_IDS) — loop bo'lmaydi
  • Har chatga cooldown (COOLDOWN soniya) — spam/ban oldini oladi
  • Bir chatda ko'p javob bo'lsa avtomatik pauza (loop breaker)
  • Aniq ma'lumotni o'ylab topmaslik uchun persona ko'rsatmasi

Javob uslubini o'zgartirish: server'da persona.txt fayl yarating.

Buyruqlar:
  .autoreply on | off | status
"""
import asyncio
import datetime
import os
import random
import time

from telethon import events

import config

from . import _state as state
from ._helpers import command, register_all
from .ai import ask_gemini

STATE = {"enabled": state.get("autoreply", False)}
_cooldown = {}       # chat_id -> oxirgi javob vaqti (monotonic)
_recent = {}         # chat_id -> [vaqtlar] (loop breaker)
_global_times = []   # barcha chatlar bo'yicha oxirgi javob vaqtlari (global limit)

COOLDOWN = 8           # bir chatga javoblar orasidagi minimal soniya (jonli suhbat)
LOOP_WINDOW = 600      # 10 daqiqa
LOOP_MAX = 20          # shu oyna ichida shu chatga maksimal avto-javob (loop breaker)
HISTORY_LIMIT = 8      # suhbat konteksti uchun oxirgi nechta xabar

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONA_FILE = os.path.join(BASE_DIR, "persona.txt")

DEFAULT_PERSONA = (
    "Sen foydalanuvchi o'rniga uning Telegram suhbatlariga javob beradigan yordamchisan. "
    "Qisqa, tabiiy va muloyim javob ber. Xabar qaysi tilda bo'lsa, o'sha tilda javob ber. "
    "Faqat javob matnining o'zini yoz — izoh yoki tirnoq qo'shma. "
    "Agar aniq ma'lumot (narx, manzil, vaqt, shaxsiy tafsilot) so'ralsa va sen bilmasang, "
    "'tez orada aniqlashtirib javob beraman' deb yoz — hech qachon ma'lumotni o'ylab topma."
)


def _within_active_hours() -> bool:
    """Hozir avto-javob ishlash soatlari ichidami (mahalliy vaqt)?"""
    lo, hi = config.ACTIVE_START, config.ACTIVE_END
    if lo == 0 and hi >= 24:
        return True
    h = (datetime.datetime.utcnow().hour + config.TZ_OFFSET) % 24
    if lo <= hi:
        return lo <= h < hi
    return h >= lo or h < hi  # tunni qamrab oladigan oraliq (masalan 22-6)


def _persona():
    if os.path.exists(PERSONA_FILE):
        try:
            with open(PERSONA_FILE, encoding="utf-8") as f:
                txt = f.read().strip()
            if txt:
                return txt
        except Exception:  # noqa: BLE001
            pass
    return DEFAULT_PERSONA


DEBUG = os.getenv("AUTOREPLY_DEBUG", "1") == "1"


def _dbg(msg):
    if DEBUG:
        print(f"[autoreply] {msg}", flush=True)


async def _on_incoming(event):
    if not STATE["enabled"]:
        return
    if not event.text:
        _dbg("skip: matn yo'q")
        return

    # #4 — Ishlash soatlari (tunda javob bermaymiz)
    if not _within_active_hours():
        _dbg("skip: ish vaqti emas")
        return

    # Shaxsiy — har doim; guruh — faqat mention/reply bo'lsa
    if event.is_private:
        # Qoralama rejimi yoqiq bo'lsa, shaxsiyga avto-javob bermaymiz
        # (draft tayyorlanadi, ikki marta ishlamasin)
        from . import autodraft
        if autodraft.STATE.get("enabled"):
            _dbg("skip: shaxsiy (autodraft ishlayapti)")
            return
    elif event.is_group and event.mentioned:
        pass
    else:
        _dbg(f"skip: guruh, mention emas (chat={event.chat_id})")
        return

    sender = await event.get_sender()
    if sender is None or getattr(sender, "bot", False):
        _dbg("skip: bot yoki sender yo'q")
        return
    # O'z akkauntlaringizga javob bermaymiz (loop oldini olish)
    if getattr(sender, "id", None) in config.OWN_ACCOUNT_IDS:
        _dbg(f"skip: o'z akkaunt (id={getattr(sender, 'id', None)})")
        return

    _dbg(f"JAVOB tayyorlanmoqda: sender={getattr(sender, 'id', None)} text={event.text[:40]!r}")

    chat_id = event.chat_id
    now = time.monotonic()

    if now - _cooldown.get(chat_id, 0) < COOLDOWN:
        _dbg(f"skip: cooldown (chat={chat_id})")
        return
    hist = [t for t in _recent.get(chat_id, []) if now - t < LOOP_WINDOW]
    if len(hist) >= LOOP_MAX:
        _dbg(f"skip: loop breaker (chat={chat_id})")
        return  # loop breaker — bu chatga vaqtincha javob bermaymiz

    # #3 — Global limit: barcha chatlar bo'yicha oynada juda ko'p javob bo'lsa to'xtaymiz
    global _global_times
    _global_times = [t for t in _global_times if now - t < config.GLOBAL_WINDOW]
    if len(_global_times) >= config.GLOBAL_MAX:
        _dbg("skip: global limit (juda ko'p javob)")
        return

    _cooldown[chat_id] = now
    hist.append(now)
    _recent[chat_id] = hist
    _global_times.append(now)

    try:
        # Suhbatni tabiiy davom ettirish uchun oxirgi xabarlarni kontekst qilamiz
        history = []
        try:
            async for msg in event.client.iter_messages(chat_id, limit=HISTORY_LIMIT):
                if msg.text:
                    who = "Men" if msg.out else "Suhbatdosh"
                    history.append(f"{who}: {msg.text}")
        except Exception:  # noqa: BLE001
            pass
        history.reverse()
        convo = "\n".join(history) if history else f"Suhbatdosh: {event.text}"
        prompt = (
            "Quyida Telegram suhbati (sen 'Men' rolidasan). "
            "Oxirgi xabarga qisqa, tabiiy davom ettirib javob ber:\n\n" + convo
        )

        reply = await ask_gemini(prompt, system=_persona())
        # Xato javoblarini (❌/⚠️/🤔 bilan boshlanadi) yubormaymiz
        if reply and reply[0] not in "❌⚠️🤔":
            # #1/#3 — odamsimon: "yozmoqda..." ko'rsatib, biroz kutib yuboramiz
            delay = random.uniform(config.HUMAN_DELAY_MIN, config.HUMAN_DELAY_MAX)
            try:
                async with event.client.action(chat_id, "typing"):
                    await asyncio.sleep(delay)
            except Exception:  # noqa: BLE001
                await asyncio.sleep(delay)
            await event.reply(reply[:4096])
            _dbg(f"YUBORILDI ({delay:.1f}s): {reply[:60]!r}")
        else:
            _dbg(f"yuborilmadi (Gemini javobi): {reply[:80]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[autoreply] xato: {e}", flush=True)


@command("autoreply", "To'liq avtomatik AI javob (on/off/status)")
async def autoreply_cmd(event):
    arg = event.pattern_match.group(1).strip().lower()
    if arg == "on":
        STATE["enabled"] = True
        state.set("autoreply", True)
        await event.edit(
            "🤖 **TO'LIQ AVTO-JAVOB YOQILDI**\n"
            "AI kelgan shaxsiy xabar va guruh mention'lariga o'zi javob yuboradi.\n"
            "⚠️ Diqqat bilan foydalaning — o'chirish: `.autoreply off`"
        )
    elif arg == "off":
        STATE["enabled"] = False
        state.set("autoreply", False)
        await event.edit("⛔ To'liq avto-javob **O'CHIRILDI**.")
    else:
        holat = "YOQILGAN 🤖" if STATE["enabled"] else "O'CHIRILGAN ⛔"
        await event.edit(
            f"ℹ️ Holat: {holat}\n"
            f"Cooldown: {COOLDOWN}s | Persona fayli: "
            f"{'bor' if os.path.exists(PERSONA_FILE) else 'yo‘q (standart)'}\n"
            f"Yoqish: `.autoreply on`"
        )


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    client.add_event_handler(_on_incoming, events.NewMessage(incoming=True))
