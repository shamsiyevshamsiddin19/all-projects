"""Akkaunt statistikalarini to'plash va yangilash plagini.

O'zi a'zo bo'lgan chatlar, guruhlar, kanallar, botlar,
hamda o'zi ochgan (creator) kanallar/guruhlar statistikasi.
"""
import asyncio
import json
import logging
import os
import time

import config
from ._helpers import command, register_all

logger = logging.getLogger("userbot.stats")
DATA_DIR = os.path.join(config.BASE_DIR, "data")


async def collect_account_stats(client):
    """Akkaunt haqidagi to'liq ma'lumotlar va chat statistikasini yig'ish."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        stats_file = os.path.join(DATA_DIR, f"stats_{config.SESSION}.json")

        me = await client.get_me()
        if not me:
            return None

        stats = {
            "account": config.SESSION,
            "updated_at": int(time.time()),
            "profile": {
                "id": me.id,
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "username": me.username or "",
                "phone": getattr(me, "phone", "") or "",
                "premium": bool(getattr(me, "premium", False)),
                "is_bot": bool(getattr(me, "bot", False)),
            },
            "summary": {
                "total_chats": 0,
                "private_chats": 0,
                "groups": 0,
                "channels": 0,
                "bots": 0,
                "unread_messages": 0,
                "created_channels_count": 0,
                "created_groups_count": 0,
                "admin_chats_count": 0,
            },
            "created_channels": [],
            "created_groups": [],
            "admin_chats": [],
            "recent_dialogs": [],
        }

        count = 0
        async for d in client.iter_dialogs(limit=300):
            count += 1
            is_user = d.is_user
            is_group = d.is_group
            is_channel = d.is_channel
            unread = d.unread_count or 0
            stats["summary"]["unread_messages"] += unread

            ent = d.entity
            is_creator = getattr(ent, "creator", False)
            admin_rights = getattr(ent, "admin_rights", None) is not None

            title = d.name or "Noma'lum"
            chat_id = d.id

            if is_user:
                if getattr(ent, "bot", False):
                    stats["summary"]["bots"] += 1
                else:
                    stats["summary"]["private_chats"] += 1
            elif is_group:
                stats["summary"]["groups"] += 1
                if is_creator:
                    stats["summary"]["created_groups_count"] += 1
                    stats["created_groups"].append({
                        "id": chat_id,
                        "title": title,
                        "unread": unread,
                    })
                elif admin_rights:
                    stats["summary"]["admin_chats_count"] += 1
                    stats["admin_chats"].append({
                        "id": chat_id,
                        "title": title,
                        "type": "group",
                    })
            elif is_channel:
                stats["summary"]["channels"] += 1
                if is_creator:
                    stats["summary"]["created_channels_count"] += 1
                    stats["created_channels"].append({
                        "id": chat_id,
                        "title": title,
                        "unread": unread,
                    })
                elif admin_rights:
                    stats["summary"]["admin_chats_count"] += 1
                    stats["admin_chats"].append({
                        "id": chat_id,
                        "title": title,
                        "type": "channel",
                    })

            if len(stats["recent_dialogs"]) < 8:
                date_str = ""
                if hasattr(d, "date") and d.date:
                    date_str = d.date.strftime("%H:%M")
                chat_type = "user"
                if is_channel:
                    chat_type = "channel"
                elif is_group:
                    chat_type = "group"
                elif getattr(ent, "bot", False):
                    chat_type = "bot"

                stats["recent_dialogs"].append({
                    "id": chat_id,
                    "title": title,
                    "type": chat_type,
                    "unread": unread,
                    "date": date_str,
                })

        stats["summary"]["total_chats"] = count

        tmp = stats_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp, stats_file)
        logger.info("Statistika muvaffaqiyatli saqlandi: %s", config.SESSION)
        return stats
    except Exception as e:  # noqa: BLE001
        logger.error("Statistika yig'ishda xatolik (%s): %s", config.SESSION, e)
        return None


@command("stats", "Akkaunt chat statistikasini yangilaydi va ko'rsatadi")
async def stats_cmd(event):
    msg = await event.edit("📊 Statistika yig'ilmoqda…")
    st = await collect_account_stats(event.client)
    if not st:
        await msg.edit("❌ Statistikani yig'ishda xatolik.")
        return

    s = st["summary"]
    text = (
        f"📊 **Statistika ({config.SESSION}):**\n\n"
        f"• Shaxsiy chatlar: **{s['private_chats']}**\n"
        f"• Guruhlar: **{s['groups']}** (Ochganim: {s['created_groups_count']})\n"
        f"• Kanallar: **{s['channels']}** (Ochganim: {s['created_channels_count']})\n"
        f"• Botlar: **{s['bots']}**\n"
        f"• O'qilmagan xabarlar: **{s['unread_messages']}**\n\n"
        f"🌐 Web panel: {config.PANEL_URL}"
    )
    await msg.edit(text)


async def _background_loop(client):
    """Har 10 daqiqada statistikani yangilab turish."""
    await asyncio.sleep(4)
    while True:
        try:
            await collect_account_stats(client)
        except Exception:  # noqa: BLE001
            pass
        await asyncio.sleep(600)


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    client.loop.create_task(_background_loop(client))
