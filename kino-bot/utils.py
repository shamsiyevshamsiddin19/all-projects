"""Umumiy yordamchi funksiyalar: caption, obuna tekshiruvi, matn normalizatsiyasi."""
import html
import re

from aiogram import Bot

import config
import db


def h(text) -> str:
    """HTML injection oldini olish."""
    return html.escape(str(text if text is not None else ""), quote=False)


def capitalize_name(name: str) -> str:
    """Har bir so'z bosh harfini kattalashtirish (mb_convert_case TITLE)."""
    return " ".join(w.capitalize() for w in (name or "").split())


def _make_hashtag(name: str) -> str:
    tag = (name or "").lower()
    tag = tag.replace("qism", "")
    tag = tag.replace("-", " ").replace("–", " ")
    tag = re.sub(r"[^\w\s]", "", tag, flags=re.UNICODE)
    tag = re.sub(r"\s+", "_", tag)
    tag = re.sub(r"_+", "_", tag)
    return tag.strip("_")


async def format_caption(name: str, code, episode=None) -> str:
    sig = await db.get_signature()
    bot_user = config.BOT_USERNAME
    txt = f"🎬 <b>{h(name)}</b>\n"
    if episode:
        txt += f"🔢 <b>Qism:</b> {h(episode)}\n"
    txt += "➖➖➖➖➖➖➖➖\n"
    txt += f"🆔 <b>Kodi:</b> <code>{h(code)}</code>\n"
    txt += "🇺🇿 <b>Til:</b> O'zbek tilida\n"
    txt += "💿 <b>Sifat:</b> Original\n"
    txt += "➖➖➖➖➖➖➖➖\n\n"
    txt += f"🤖 <b>Botga o'tish:</b> @{h(bot_user)}\n"
    txt += f"{h(sig)}\n\n"
    txt += f"#{_make_hashtag(name)}"
    return txt


def normalize_search_text(s: str) -> str:
    s = (s or "").strip().lower()
    for ch in ["’", "`", "ʻ", "ʼ", "‘", "´"]:
        s = s.replace(ch, "'")
    s = re.sub(r"[^a-z0-9а-яёқғҳў' ]", " ", s, flags=re.IGNORECASE | re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


async def check_sub(bot: Bot, user_id: int):
    """True agar hammasiga obuna bo'lsa, aks holda yetishmayotgan kanallar ro'yxati."""
    if user_id in config.ADMIN_IDS:
        return True
    if await db.get_force_sub() == 0:
        return True

    channels = await db.fetch("SELECT channel_id, title, link FROM channels")
    if not channels:
        return True

    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["channel_id"], user_id)
            status = getattr(member, "status", None)
            if status not in ("creator", "administrator", "member", "restricted"):
                missing.append({"text": ch["title"], "url": ch["link"]})
        except Exception:
            # Fail-closed: xatolik bo'lsa obuna talab qilinadi
            missing.append({"text": ch["title"], "url": ch["link"]})
    return True if not missing else missing


def deep_link(code) -> str:
    return f"https://t.me/{config.BOT_USERNAME}?start=code_{code}"
