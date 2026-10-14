"""Yarim-avtomatik AI javob rejimi.

Yoqilganda (.autoai on) shaxsiy chatga kelgan xabarga Gemini javob taklifi
tayyorlaydi va uni SIZNING "Saved Messages"ingizga yuboradi. Siz tasdiqlaguningizcha
(.ok) hech kimga hech narsa yuborilmaydi.

Buyruqlar:
  .autoai on | off | status
  .ok [tahrirlangan matn]   — taklifga javoban: haqiqiy javobni yuboradi
  .no                       — taklifga javoban: taklifni bekor qiladi
"""
from telethon import events

from . import _state as state
from ._helpers import command, register_all
from .ai import ask_gemini

# Rejim holati va kutayotgan takliflar
STATE = {"enabled": state.get("autoai", False)}
# {saved_message_id: {"chat_id": ..., "target_msg_id": ..., "text": ..., "who": ...}}
PENDING = {}

SYSTEM = (
    "Sen foydalanuvchi o'rniga uning shaxsiy suhbatlariga qisqa, tabiiy, muloyim "
    "javob YOZIB BERADIGAN yordamchisan. Faqat javob matnining o'zini yoz — "
    "hech qanday izoh, tirnoq yoki qo'shimcha so'z qo'shma. Xabar qaysi tilda "
    "bo'lsa, o'sha tilda javob ber."
)


async def _on_incoming(event):
    """Kelgan shaxsiy xabarga javob taklifi tayyorlaydi."""
    if not STATE["enabled"]:
        return
    if not event.text:
        return

    # Shaxsiy chat — har doim; guruh — faqat siz mention/reply qilinganda
    if event.is_private:
        joy = "shaxsiy"
    elif event.is_group and event.mentioned:
        joy = "guruh"
    else:
        return

    sender = await event.get_sender()
    # Bot yoki o'zimiz yozgan xabarlarga javob taklifi tayyorlamaymiz
    if sender is None or getattr(sender, "bot", False):
        return

    name = getattr(sender, "first_name", "") or "Foydalanuvchi"
    if joy == "guruh":
        chat = await event.get_chat()
        title = getattr(chat, "title", "guruh")
        name = f"{name} ({title})"

    try:
        suggestion = await ask_gemini(event.text, system=SYSTEM)
        card = (
            f"🤖 **Yangi xabar** — {name}\n"
            f"💬 {event.text[:500]}\n\n"
            f"📝 **Taklif javob:**\n{suggestion[:1500]}\n\n"
            f"✅ Yuborish → shu xabarga javoban `.ok`\n"
            f"✏️ Tahrirlab → `.ok yangi matn`\n"
            f"❌ Bekor → `.no`"
        )
        # Xabar matnidagi maxsus belgilar formatlashni buzmasligi uchun
        # oddiy (parse_mode=None) rejimda yuboramiz.
        sent = await event.client.send_message("me", card, parse_mode=None)
        PENDING[sent.id] = {
            "chat_id": event.chat_id,
            "target_msg_id": event.id,
            "text": suggestion,
            "who": name,
        }
    except Exception as e:  # noqa: BLE001 — bitta xato tinglovchini o'ldirmasin
        print(f"[autoai] xato: {e}")


@command("autoai", "Yarim-avtomatik AI javob rejimi (on/off/status)")
async def autoai_cmd(event):
    arg = event.pattern_match.group(1).strip().lower()
    if arg == "on":
        STATE["enabled"] = True
        state.set("autoai", True)
        await event.edit(
            "✅ Yarim-avtomatik AI javob **YOQILDI**.\n"
            "Kelgan shaxsiy xabarlarga javob taklifi Saved Messages'ga tushadi.\n"
            "Yuborish uchun taklifga `.ok` deb javob bering."
        )
    elif arg == "off":
        STATE["enabled"] = False
        state.set("autoai", False)
        PENDING.clear()
        await event.edit("⛔ Yarim-avtomatik AI javob **O'CHIRILDI**.")
    else:
        holat = "YOQILGAN ✅" if STATE["enabled"] else "O'CHIRILGAN ⛔"
        await event.edit(
            f"ℹ️ Holat: {holat}\n"
            f"Kutayotgan takliflar: {len(PENDING)} ta\n\n"
            f"Yoqish: `.autoai on` | O'chirish: `.autoai off`"
        )


@command("ok", "Taklif javobni haqiqatan yuboradi (taklifga javoban)")
async def ok_cmd(event):
    reply = await event.get_reply_message()
    if not reply or reply.id not in PENDING:
        await event.edit("Buni bir AI taklifiga **javoban** yozing.")
        return
    entry = PENDING.pop(reply.id)
    # Tahrirlangan matn berilgan bo'lsa o'shani, aks holda taklifni yuboramiz
    edited = event.pattern_match.group(1).strip()
    text = edited or entry["text"]
    try:
        await event.client.send_message(
            entry["chat_id"], text, reply_to=entry["target_msg_id"]
        )
        await event.edit(f"✅ **{entry['who']}**ga yuborildi:\n\n{text}")
    except Exception as e:  # noqa: BLE001
        await event.edit(f"❌ Yuborilmadi: {e}")


@command("no", "Taklifni bekor qiladi (taklifga javoban)")
async def no_cmd(event):
    reply = await event.get_reply_message()
    if reply and reply.id in PENDING:
        PENDING.pop(reply.id)
        await event.edit("❌ Taklif bekor qilindi.")
    else:
        await event.edit("Bekor qilish uchun bir AI taklifiga **javoban** yozing.")


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    # Kelgan xabarlarni tinglash uchun alohida handler
    client.add_event_handler(_on_incoming, events.NewMessage(incoming=True))
