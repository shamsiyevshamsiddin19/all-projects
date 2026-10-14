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
AVATARS_DIR = os.path.join(DATA_DIR, "avatars")
AVATAR_CACHE_TTL = 86400 * 3  # 3 kun


async def _save_avatar(client, entity, file_id):
    """Telegram profil yoki chat rasmini kichik hajmda yuklab olish va saqlash."""
    if not entity or not file_id:
        return False
    # Agar chat/userda rasm bo'lmasa, ortiqcha so'rov yubormaymiz
    if not getattr(entity, "photo", None):
        return False

    dest = os.path.join(AVATARS_DIR, f"{file_id}.jpg")
    try:
        if (
            os.path.exists(dest)
            and os.path.getsize(dest) > 0
            and (time.time() - os.path.getmtime(dest) < AVATAR_CACHE_TTL)
        ):
            return True
        res = await asyncio.wait_for(
            client.download_profile_photo(entity, file=dest, download_big=False),
            timeout=4.0,
        )
        return bool(res and os.path.exists(dest) and os.path.getsize(dest) > 0)
    except Exception as e:  # noqa: BLE001
        logger.debug("Avatar yuklashda xatolik (%s): %s", file_id, e)
        return False


async def collect_account_stats(client):
    """Akkaunt haqidagi to'liq ma'lumotlar va chat statistikasini yig'ish."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(AVATARS_DIR, exist_ok=True)
        stats_file = os.path.join(DATA_DIR, f"stats_{config.SESSION}.json")

        me = await client.get_me()
        if not me:
            return None

        # O'z profil rasmini yuklab olish (ham me.id, ham accX nomi bilan)
        await _save_avatar(client, me, me.id)
        await _save_avatar(client, me, config.SESSION)

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
                "avatar": f"/api/avatar/{me.id}",
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

        avatar_queue = []
        count = 0
        async for d in client.iter_dialogs(limit=600):
            count += 1
            unread = d.unread_count or 0
            stats["summary"]["unread_messages"] += unread

            ent = d.entity
            is_creator = getattr(ent, "creator", False)
            admin_rights = getattr(ent, "admin_rights", None) is not None
            is_megagroup = bool(getattr(ent, "megagroup", False))
            username = getattr(ent, "username", "") or ""

            title = d.name or "Noma'lum"
            chat_id = d.id

            # Aniq turlarga ajratish:
            # Telegramda superguruhlar Channel(megagroup=True) hisoblanadi.
            if d.is_user:
                if getattr(ent, "bot", False):
                    stats["summary"]["bots"] += 1
                else:
                    stats["summary"]["private_chats"] += 1
            elif d.is_group or is_megagroup:
                stats["summary"]["groups"] += 1
                if is_creator:
                    stats["summary"]["created_groups_count"] += 1
                    stats["created_groups"].append({
                        "id": chat_id,
                        "title": title,
                        "username": username,
                        "unread": unread,
                        "avatar": f"/api/avatar/{chat_id}",
                    })
                    avatar_queue.append((ent, chat_id))
                elif admin_rights:
                    stats["summary"]["admin_chats_count"] += 1
                    stats["admin_chats"].append({
                        "id": chat_id,
                        "title": title,
                        "username": username,
                        "type": "group",
                        "avatar": f"/api/avatar/{chat_id}",
                    })
                    avatar_queue.append((ent, chat_id))
            elif d.is_channel and not is_megagroup:
                stats["summary"]["channels"] += 1
                if is_creator:
                    stats["summary"]["created_channels_count"] += 1
                    stats["created_channels"].append({
                        "id": chat_id,
                        "title": title,
                        "username": username,
                        "unread": unread,
                        "avatar": f"/api/avatar/{chat_id}",
                    })
                    avatar_queue.append((ent, chat_id))
                elif admin_rights:
                    stats["summary"]["admin_chats_count"] += 1
                    stats["admin_chats"].append({
                        "id": chat_id,
                        "title": title,
                        "username": username,
                        "type": "channel",
                        "avatar": f"/api/avatar/{chat_id}",
                    })
                    avatar_queue.append((ent, chat_id))

            if len(stats["recent_dialogs"]) < 16:
                date_str = ""
                if hasattr(d, "date") and d.date:
                    date_str = d.date.strftime("%H:%M")
                chat_type = "user"
                if d.is_channel and not is_megagroup:
                    chat_type = "channel"
                elif d.is_group or is_megagroup:
                    chat_type = "group"
                elif getattr(ent, "bot", False):
                    chat_type = "bot"

                stats["recent_dialogs"].append({
                    "id": chat_id,
                    "title": title,
                    "username": username,
                    "type": chat_type,
                    "unread": unread,
                    "date": date_str,
                    "avatar": f"/api/avatar/{chat_id}",
                })
                avatar_queue.append((ent, chat_id))

        stats["summary"]["total_chats"] = count

        # Dastlabki eng muhim suhbatlar rasmlarini tezkor yuklab olish
        for ent, cid in avatar_queue[:15]:
            await _save_avatar(client, ent, cid)

        # Qolgan chat rasmlarini fon rejimida sekin yuklab olish (Telegram limitini buzmaslik uchun)
        if len(avatar_queue) > 15:
            async def _bg_avatars(items):
                for e, cid in items:
                    await _save_avatar(client, e, cid)
                    await asyncio.sleep(0.05)

            client.loop.create_task(_bg_avatars(avatar_queue[15:]))

        tmp = stats_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp, stats_file)
        logger.info("Statistika va avatarlar muvaffaqiyatli saqlandi: %s", config.SESSION)
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
    """Fon rejimida har 10 daqiqada yoki yangilash flag fayli paydo bo'lganda statistika yig'ish."""
    await asyncio.sleep(4)
    # Dastlabki ishga tushganda yig'ish
    await collect_account_stats(client)

    flag_acc = os.path.join(DATA_DIR, f"refresh_stats_{config.SESSION}.flag")
    flag_all = os.path.join(DATA_DIR, "refresh_stats_all.flag")

    last_periodic = time.time()
    last_flag_mtime = 0.0

    while True:
        await asyncio.sleep(3)
        now = time.time()
        need_refresh = False

        if os.path.exists(flag_acc):
            try:
                os.remove(flag_acc)
            except Exception:  # noqa: BLE001
                pass
            need_refresh = True
        elif os.path.exists(flag_all):
            try:
                mtime = os.path.getmtime(flag_all)
                if mtime > last_flag_mtime:
                    last_flag_mtime = mtime
                    need_refresh = True
            except Exception:  # noqa: BLE001
                pass

        if need_refresh or (now - last_periodic >= 600):
            try:
                await collect_account_stats(client)
            except Exception as e:  # noqa: BLE001
                logger.error("Statistika yig'ishda xatolik: %s", e)
            last_periodic = now


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    client.loop.create_task(_background_loop(client))
