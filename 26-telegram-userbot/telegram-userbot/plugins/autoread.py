"""Guruh / kanal / bot xabarlarini avtomatik va qo'lda o'qish.

Avto-o'qish (doimiy) har bir tur uchun ALOHIDA yoqiladi: guruh, kanal, bot.
Yoqilgan turlar uchun:
  1) Yangi kelgan xabar darhol o'qilgan bo'ladi.
  2) Har 3 daqiqada o'qilmaganlari qayta o'qilgan qilinadi.
Shaxsiy (tirik odam) xabarlariga tegilmaydi.

Buyruqlar:
  .autoread status                — holat
  .autoread channels [on|off]     — kanallarni avto-o'qish
  .autoread groups   [on|off]     — guruhlarni avto-o'qish
  .autoread bots     [on|off]     — botlarni avto-o'qish
  .autoread on | off              — hammasini birdan yoqish/o'chirish

  .readall / .readgroups / .readchannels / .readbots  — hozir bir marta o'qish
"""
import asyncio

from telethon import events

from . import _state as state
from ._helpers import command, register_all

ALL_KINDS = {"group", "channel", "bot"}
# buyruqdagi nom -> ichki tur
CATS = {"groups": "group", "channels": "channel", "bots": "bot"}
_LABEL = {"group": "👥 Guruhlar", "channel": "📢 Kanallar", "bot": "🤖 Botlar"}

SWEEP_INTERVAL = 180
FIRST_SWEEP_DELAY = 15

# Yoqilgan turlar to'plami (diskda saqlanadi). Eski "autoread=true" bo'lsa hammasi.
if state.get("autoread_kinds") is not None:
    KINDS = set(state.get("autoread_kinds"))
elif state.get("autoread"):
    KINDS = set(ALL_KINDS)
else:
    KINDS = set()


def _persist():
    state.set("autoread_kinds", sorted(KINDS))
    state.set("autoread", bool(KINDS))  # moslik uchun


async def _sweep(client, kinds) -> int:
    """kinds ichidagi turlar bo'yicha o'qilmagan chatlarni o'qilgan qiladi."""
    if not kinds:
        return 0
    count = 0
    async for dialog in client.iter_dialogs():
        try:
            if not dialog.unread_count:
                continue
            is_bot = dialog.is_user and getattr(dialog.entity, "bot", False)
            is_channel = dialog.is_channel and not dialog.is_group
            match = (
                ("group" in kinds and dialog.is_group)
                or ("channel" in kinds and is_channel)
                or ("bot" in kinds and is_bot)
            )
            if match:
                await client.send_read_acknowledge(dialog.id)
                count += 1
        except Exception:  # noqa: BLE001
            pass
    return count


async def _sweeper(client):
    await asyncio.sleep(FIRST_SWEEP_DELAY)
    while True:
        if KINDS:
            try:
                n = await _sweep(client, KINDS)
                if n:
                    print(f"[autoread] davriy o'qish: {n} ta chat", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[autoread] sweeper xato: {e}", flush=True)
        await asyncio.sleep(SWEEP_INTERVAL)


async def _event_kind(event):
    if event.is_group:
        return "group"
    if event.is_channel:
        return "channel"
    if event.is_private:
        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return "bot"
    return None


async def _on_incoming(event):
    if not KINDS:
        return
    try:
        kind = await _event_kind(event)
        if kind in KINDS:
            await event.mark_read()
    except Exception as e:  # noqa: BLE001
        print(f"[autoread] xato: {e}", flush=True)


def _status_text():
    if not KINDS:
        yoq = "hech biri (o'chiq)"
    else:
        yoq = ", ".join(_LABEL[k] for k in sorted(KINDS))
    return (
        f"👁 **Avto-o'qish holati**\n"
        f"Yoqilgan: {yoq}\n\n"
        f"`.autoread channels` — kanallarni yoqish\n"
        f"`.autoread groups` / `.autoread bots`\n"
        f"`.autoread channels off` — o'chirish | `.autoread off` — hammasi"
    )


@command("autoread", "Guruh/kanal/bot avto-o'qish (channels/groups/bots on/off)")
async def autoread_cmd(event):
    parts = event.pattern_match.group(1).strip().lower().split()

    if not parts or parts[0] == "status":
        await event.edit(_status_text())
        return

    if parts[0] == "on":
        KINDS.update(ALL_KINDS)
        _persist()
        await event.edit("👁 Hammasi YOQILDI (guruh, kanal, bot).\n\n" + _status_text())
        return
    if parts[0] == "off":
        KINDS.clear()
        _persist()
        await event.edit("⛔ Avto-o'qish butunlay O'CHIRILDI.\n\n" + _status_text())
        return

    if parts[0] in CATS:
        kind = CATS[parts[0]]
        turn_off = len(parts) > 1 and parts[1] in ("off", "0", "no")
        if turn_off:
            KINDS.discard(kind)
            msg = f"{_LABEL[kind]} avto-o'qish ⚪️ o'chirildi."
        else:
            KINDS.add(kind)
            msg = f"{_LABEL[kind]} avto-o'qish 🟢 yoqildi."
        _persist()
        await event.edit(msg + "\n\n" + _status_text())
        return

    await event.edit(_status_text())


@command("readall", "Barcha guruh/kanal/bot chatlarini o'qiydi")
async def readall_cmd(event):
    await event.edit("👁 O'qilmoqda...")
    n = await _sweep(event.client, ALL_KINDS)
    await event.edit(f"✅ {n} ta guruh/kanal/bot chati o'qildi.")


@command("readgroups", "Faqat guruhlarni o'qiydi")
async def readgroups_cmd(event):
    await event.edit("👥 Guruhlar o'qilmoqda...")
    n = await _sweep(event.client, {"group"})
    await event.edit(f"✅ {n} ta guruh o'qildi.")


@command("readchannels", "Faqat kanallarni o'qiydi")
async def readchannels_cmd(event):
    await event.edit("📢 Kanallar o'qilmoqda...")
    n = await _sweep(event.client, {"channel"})
    await event.edit(f"✅ {n} ta kanal o'qildi.")


@command("readbots", "Faqat bot chatlarini o'qiydi")
async def readbots_cmd(event):
    await event.edit("🤖 Botlar o'qilmoqda...")
    n = await _sweep(event.client, {"bot"})
    await event.edit(f"✅ {n} ta bot chati o'qildi.")


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    client.add_event_handler(_on_incoming, events.NewMessage(incoming=True))
    asyncio.create_task(_sweeper(client))
