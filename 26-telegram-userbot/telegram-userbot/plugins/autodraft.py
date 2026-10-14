"""Shaxsiy chatga javob QORALAMASINI tayyorlab qo'yadi (yubormaydi).

Yoqilganda (.autodraft on) shaxsiy xabar kelsa, Gemini javob matnini o'sha
chatning yozish qatoriga (draft) tayyorlab qo'yadi. Siz o'qib, tahrirlab,
o'zingiz Send bosasiz. Hech narsa avtomatik yuborilmaydi.

Buyruqlar:
  .autodraft on | off | status
"""
import os

from telethon import events
from telethon.tl.functions.messages import SaveDraftRequest

import config

from . import _state as state
from ._helpers import command, register_all
from .ai import ask_gemini

STATE = {"enabled": state.get("autodraft", False)}

HISTORY_LIMIT = 25
_PERSONA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "persona.txt"
)
_DEFAULT_PERSONA = (
    "Sen foydalanuvchi o'rniga uning shaxsiy suhbatlariga qisqa, tabiiy va muloyim "
    "javob matnini yozadigan yordamchisan. Faqat javob matnini yoz. Xabar qaysi "
    "tilda bo'lsa o'sha tilda javob ber. Aniq narsani (vaqt, pul, va'da) bilmasang "
    "o'ylab topma — 'tez orada aniq javob beraman' deb yoz."
)


# Qoralama rejimi — foydalanuvchi yuborishdan oldin ko'radi, shuning uchun
# AI to'liq, jonli va aniq javob yozsin (qochmasin).
_DRAFT_MODE = (
    "=== QORALAMA REJIMI (JUDA MUHIM) ===\n"
    "Bu javob QORALAMA — foydalanuvchi uni yuborishdan OLDIN o'qiydi va tahrirlaydi. "
    "Shuning uchun:\n"
    "- TO'LIQ, aniq va jonli javob yoz. Savolga to'g'ridan-to'g'ri javob ber.\n"
    "- Reja/vaqt/taklifga tabiiy javob ber (masalan: 'Ha, chiqamiz! Soat 5 da-chi?'). "
    "'Keyinroq aytaman' deb QOCHMA — iloji boricha haqiqiy, foydali javob ber.\n"
    "- Faqat hech qanday yo'l bilan bilishing mumkin bo'lmagan aniq shaxsiy faktni "
    "(masalan hech qачon aytilmagan manzil yoki parol) to'qima. Qolgan hamma narsada "
    "erkin, aqlli va kontekstga mos javob ber.\n"
    "- Suhbatdoshga va suhbat ohangiga qarab jonli, tabiiy yoz."
)


def _persona():
    try:
        with open(_PERSONA_FILE, encoding="utf-8") as f:
            txt = f.read().strip()
        if txt:
            base = txt
        else:
            base = _DEFAULT_PERSONA
    except Exception:  # noqa: BLE001
        base = _DEFAULT_PERSONA
    return base + "\n\n" + _DRAFT_MODE


async def _on_incoming(event):
    if not STATE["enabled"]:
        return
    if not event.is_private or not event.text:
        return
    sender = await event.get_sender()
    if sender is None or getattr(sender, "bot", False):
        return
    if getattr(sender, "id", None) in config.OWN_ACCOUNT_IDS:
        return

    try:
        # Suhbatdosh haqida ma'lumot (kimga qarab moslash uchun)
        sender_name = (getattr(sender, "first_name", "") or "").strip()
        last_name = (getattr(sender, "last_name", "") or "").strip()
        if last_name:
            sender_name = f"{sender_name} {last_name}".strip()
        sender_name = sender_name or "Suhbatdosh"
        username = getattr(sender, "username", None)
        is_contact = bool(getattr(sender, "contact", False))

        # Suhbat tarixini yig'amiz — 'Men' (siz) va suhbatdosh ismi bilan
        history = []
        owner_has_written = False
        async for msg in event.client.iter_messages(event.chat_id, limit=HISTORY_LIMIT):
            if msg.text:
                if msg.out:
                    who = "Men"
                    owner_has_written = True
                else:
                    who = sender_name
                history.append(f"{who}: {msg.text}")
        history.reverse()
        convo = "\n".join(history) if history else f"{sender_name}: {event.text}"

        # Uslub ko'rsatmasi: agar oldin yozgan bo'lsangiz — o'sha uslubni taqlid qil
        if owner_has_written:
            style = (
                "'Men' bu suhbatda oldin qanday yozgan bo'lsa — o'sha til, ohang, "
                "rasmiylik/samimiylik darajasi va so'z uslubini AYNAN saqlab davom ettir."
            )
        else:
            style = (
                "Bu suhbatdosh bilan avvalgi yozishmalar yo'q — muloyim, tabiiy va "
                "o'rtacha samimiy uslubda yoz."
            )

        munosabat = "tanishingiz (kontaktda bor)" if is_contact else "kontaktda yo'q (ehtimol notanish)"

        prompt = (
            f"Suhbatdosh: {sender_name}"
            + (f" (@{username})" if username else "")
            + f" — {munosabat}.\n\n"
            "Quyida shu odam bilan Telegram suhbati. 'Men' — bu javob beruvchi (sen).\n\n"
            "VAZIFA: suhbatdoshning ENG OXIRGI xabariga aynan mos, aniq va tabiiy "
            "javob matnini tayyorla. Qoidalar:\n"
            f"- {style}\n"
            "- Suhbat kontekstini diqqat bilan hisobga ol — mavzudan chetga chiqma, "
            "avval nima gaplashilganini yodda tut.\n"
            "- Aniq narsa (vaqt, joy, pul, va'da) so'ralsa va bilmasang — o'ylab topma, "
            "'tez orada aniq javob beraman' deb yoz.\n"
            "- Xabar qaysi tilda bo'lsa, o'sha tilda javob ber.\n"
            "- Faqat javob matnining o'zini yoz — izoh, tirnoq yoki qo'shimcha so'z qo'shma.\n\n"
            f"=== SUHBAT ===\n{convo}"
        )
        reply = await ask_gemini(prompt, system=_persona())
        if reply and reply[0] not in "❌⚠️🤔":
            # Javobni chatning yozish qatoriga QORALAMA qilib qo'yamiz (yubormaymiz)
            await event.client(SaveDraftRequest(
                peer=await event.get_input_chat(),
                message=reply[:4096],
                no_webpage=True,
            ))
            print(f"[autodraft] qoralama tayyor: {reply[:50]!r}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[autodraft] xato: {e}", flush=True)


@command("autodraft", "Shaxsiy chatga javob qoralamasini tayyorlaydi (on/off/status)")
async def autodraft_cmd(event):
    arg = event.pattern_match.group(1).strip().lower()
    if arg == "on":
        STATE["enabled"] = True
        state.set("autodraft", True)
        await event.edit(
            "✍️ **Qoralama rejimi YOQILDI**\n"
            "Shaxsiy xabarga javob matni o'sha chatning yozish qatoriga tayyorlab "
            "qo'yiladi. O'qib, tahrirlab, o'zingiz Send bosasiz — avtomat yuborilmaydi."
        )
    elif arg == "off":
        STATE["enabled"] = False
        state.set("autodraft", False)
        await event.edit("✍️ Qoralama rejimi **O'CHIRILDI**.")
    else:
        holat = "YOQILGAN ✍️" if STATE["enabled"] else "O'CHIRILGAN ⛔"
        await event.edit(f"ℹ️ Qoralama rejimi: {holat}\nYoqish: `.autodraft on`")


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    client.add_event_handler(_on_incoming, events.NewMessage(incoming=True))
