"""Asosiy buyruqlar: ping, alive, id."""
import time

from ._helpers import command, register_all


@command("ping", "Javob tezligini tekshiradi")
async def ping(event):
    start = time.perf_counter()
    msg = await event.edit("Pinging...")
    ms = (time.perf_counter() - start) * 1000
    await msg.edit(f"🏓 Pong! `{ms:.0f} ms`")


@command("alive", "Userbot ishlayotganini ko'rsatadi")
async def alive(event):
    await event.edit(
        "**Userbot ishlayapti** ✅\n"
        "• Kutubxona: Telethon\n"
        "• Yordam: `.help`"
    )


@command("id", "Chat / foydalanuvchi ID sini beradi")
async def get_id(event):
    reply = await event.get_reply_message()
    text = f"**Chat ID:** `{event.chat_id}`"
    if reply:
        text += f"\n**Foydalanuvchi ID:** `{reply.sender_id}`"
    await event.edit(text)


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
