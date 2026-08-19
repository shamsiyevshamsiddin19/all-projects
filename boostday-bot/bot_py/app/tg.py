"""Telegram API qatlami: so'rovlar, xabar yuborish, klaviaturalar, media."""

from __future__ import annotations

import json
import logging

import httpx

from .config import settings
from .helpers import bot_signature, escape_html

logger = logging.getLogger("boostday")


def telegram(method: str, params: dict | None = None) -> dict | None:
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/{method}"
    try:
        resp = httpx.post(url, data=params or {}, timeout=30)
        decoded = resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("TELEGRAM_REQUEST_ERROR %s: %s", method, e)
        return None

    if not decoded or not decoded.get("ok"):
        logger.warning("TELEGRAM_API_ERROR %s: %s", method, decoded)
    return decoded


def telegram_upload(method: str, files: dict, data: dict) -> dict | None:
    """Multipart fayl yuklash (sendPhoto/sendVideo/... uchun) — `telegram()` dan farqli, files= bilan."""
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/{method}"
    try:
        resp = httpx.post(url, data=data, files=files, timeout=60)
        decoded = resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("TELEGRAM_UPLOAD_ERROR %s: %s", method, e)
        return None
    if not decoded or not decoded.get("ok"):
        logger.warning("TELEGRAM_UPLOAD_API_ERROR %s: %s", method, decoded)
    return decoded


def send_message(chat_id, text: str, reply_markup: dict | None = None, parse_mode: str = "HTML") -> dict | None:
    params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        params["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    return telegram("sendMessage", params)


def edit_message(chat_id, message_id, text: str, reply_markup: dict | None = None, parse_mode: str = "HTML") -> dict | None:
    params = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        params["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    return telegram("editMessageText", params)


def answer_callback(callback_id: str, text: str = "") -> None:
    telegram("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": False})


def delete_message(chat_id, message_id) -> None:
    telegram("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


# --- Reply klaviaturalari ---

MINIAPP_BUTTON_TEXT = "🚀 Mini App (tez rejalash)"


def keyboard_main() -> dict:
    keyboard = []
    if settings.MINIAPP_URL:
        # Oddiy matn tugma — bosilganda bot inline (web_app) tugmali xabar yuboradi.
        # Reply-keyboard'dagi web_app tugmasi ba'zi Telegram klientlarida initData'ni
        # to'g'ri uzatmaydi; inline tugma esa barcha versiyalarda ishonchli ishlaydi.
        keyboard.append([MINIAPP_BUTTON_TEXT])
    keyboard += [
        ["📢 Kanal ulash", "📢 Kanallarim"],
        ["📅 Reja tuzish", "🎗 Eslatma qo‘shish"],
        ["🗓 Kalendar reja", "📂 Mening rejalarim"],
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}


def miniapp_inline_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "🚀 Ochish", "web_app": {"url": settings.MINIAPP_URL}}]]}


def set_chat_menu_button() -> None:
    """Bot chat menu tugmasini Mini App'ga o'rnatadi (barcha foydalanuvchilar uchun)."""
    if not settings.MINIAPP_URL:
        return
    telegram("setChatMenuButton", {"menu_button": json.dumps(
        {"type": "web_app", "text": "Mini App", "web_app": {"url": settings.MINIAPP_URL}},
        ensure_ascii=False,
    )})


FINISH_TEXT = "✅ Tugatish"
CANCEL_TEXT = "❌ Bekor qilish"


def keyboard_cancel() -> dict:
    return {"keyboard": [[FINISH_TEXT, CANCEL_TEXT]], "resize_keyboard": True}


def only_cancel_keyboard() -> dict:
    return {"keyboard": [[CANCEL_TEXT]], "resize_keyboard": True}


def inline_channels(channels: list, prefix: str) -> dict:
    rows = []
    for ch in channels:
        rows.append([{
            "text": f"{ch['channel_name']} ({ch['channel_id']})",
            "callback_data": f"{prefix}:{ch['id']}",
        }])
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


# --- Inline sana/vaqt tanlagichlar ---

def build_inline_year_picker(flow_key: str) -> dict:
    from .helpers import now

    current_year = now().year
    rows, row = [], []
    for y in range(current_year - 2, current_year + 6):
        row.append({"text": str(y), "callback_data": f"pick_year:{flow_key}:{y}"})
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


def build_inline_month_picker(flow_key: str, year: int) -> dict:
    from .helpers import month_name_uz

    rows, row = [], []
    for m in range(1, 13):
        row.append({"text": month_name_uz(m), "callback_data": f"pick_month:{flow_key}:{year}:{m}"})
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "⬅️ Yilga qaytish", "callback_data": f"pick_date_back_year:{flow_key}"}])
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


def build_inline_day_picker(flow_key: str, year: int, month: int) -> dict:
    from .helpers import days_in_month

    rows, row = [], []
    for d in range(1, days_in_month(year, month) + 1):
        row.append({"text": str(d), "callback_data": f"pick_day:{flow_key}:{year}:{month}:{d}"})
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "⬅️ Oyga qaytish", "callback_data": f"pick_date_back_month:{flow_key}:{year}"}])
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


def build_inline_hour_picker(flow_key: str) -> dict:
    rows, row = [], []
    for h in range(24):
        row.append({"text": f"{h:02d}", "callback_data": f"pick_hour:{flow_key}:{h}"})
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


def build_inline_minute_picker(flow_key: str, hour: int) -> dict:
    rows, row = [], []
    for m in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
        row.append({"text": f"{m:02d}", "callback_data": f"pick_minute:{flow_key}:{hour}:{m}"})
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "⬅️ Soatga qaytish", "callback_data": f"pick_time_back_hour:{flow_key}"}])
    rows.append([{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}])
    return {"inline_keyboard": rows}


# --- Chat ma'lumotlari ---

def get_chat_info_multi(candidates: list) -> dict | None:
    for candidate in candidates:
        r = telegram("getChat", {"chat_id": candidate})
        if r and r.get("ok") and r.get("result"):
            return r["result"]
    return None


def is_supported_target_chat(chat: dict | None) -> bool:
    if not chat or not chat.get("type"):
        return False
    return str(chat["type"]) in ("channel", "group", "supergroup")


def target_chat_type_label(chat: dict | None) -> str:
    if not chat or not chat.get("type"):
        return "noma'lum"
    t = str(chat["type"])
    if t == "channel":
        return "kanal"
    if t in ("group", "supergroup"):
        return "guruh"
    return t


def bot_is_admin(channel_id: str) -> bool:
    bot_id = int(settings.BOT_ID)
    if not bot_id:
        return False
    member = telegram("getChatMember", {"chat_id": channel_id, "user_id": bot_id})
    if member and member.get("ok") and member.get("result", {}).get("status"):
        return member["result"]["status"] in ("administrator", "creator")
    admins = telegram("getChatAdministrators", {"chat_id": channel_id})
    if not admins or not admins.get("ok") or not admins.get("result"):
        return False
    for admin in admins["result"]:
        u = admin.get("user", {})
        if u.get("id") and int(u["id"]) == bot_id:
            return True
    return False


# --- Media ---

def extract_media_item(message: dict) -> dict | None:
    caption = message.get("caption", "") or ""
    media_group_id = str(message["media_group_id"]) if message.get("media_group_id") else None

    if message.get("text"):
        return {"type": "text", "text": message["text"], "media_group_id": None}
    if message.get("photo"):
        photo = message["photo"][-1]
        return {"type": "photo", "file_id": photo["file_id"], "caption": caption, "media_group_id": media_group_id}
    if message.get("video"):
        return {"type": "video", "file_id": message["video"]["file_id"], "caption": caption, "media_group_id": media_group_id}
    if message.get("audio"):
        return {"type": "audio", "file_id": message["audio"]["file_id"], "caption": caption, "media_group_id": media_group_id}
    if message.get("document"):
        return {"type": "document", "file_id": message["document"]["file_id"], "caption": caption, "media_group_id": media_group_id}
    return None


def send_plan_items(chat_id, items: list, extra_top: str | None = None) -> None:
    if extra_top:
        send_message(chat_id, extra_top)

    buffer: list = []

    def flush():
        nonlocal buffer
        if not buffer:
            return
        if len(buffer) == 1:
            one = buffer[0]
            if one["type"] == "photo":
                telegram("sendPhoto", {"chat_id": chat_id, "photo": one["file_id"],
                                       "caption": one.get("caption", ""), "parse_mode": "HTML"})
            elif one["type"] == "video":
                telegram("sendVideo", {"chat_id": chat_id, "video": one["file_id"],
                                       "caption": one.get("caption", ""), "parse_mode": "HTML"})
            buffer = []
            return
        media = []
        for index, m in enumerate(buffer):
            row = {"type": m["type"], "media": m["file_id"]}
            if index == 0 and m.get("caption"):
                row["caption"] = m["caption"]
                row["parse_mode"] = "HTML"
            media.append(row)
        telegram("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media, ensure_ascii=False)})
        buffer = []

    for item in items:
        t = item.get("type", "text")
        if t in ("photo", "video"):
            buffer.append(item)
            continue
        flush()
        if t == "text":
            send_message(chat_id, item.get("text", ""))
        elif t == "audio":
            telegram("sendAudio", {"chat_id": chat_id, "audio": item["file_id"],
                                   "caption": item.get("caption", ""), "parse_mode": "HTML"})
        elif t == "document":
            telegram("sendDocument", {"chat_id": chat_id, "document": item["file_id"],
                                      "caption": item.get("caption", ""), "parse_mode": "HTML"})
    flush()


def _collect_challenge_body_parts(items: list) -> list[str]:
    parts = []
    for item in items:
        t = item.get("type", "")
        if t == "text" and item.get("text"):
            txt = item["text"].strip()
            if txt:
                parts.append(txt)
        if t in ("photo", "video", "audio", "document") and item.get("caption"):
            cap = item["caption"].strip()
            if cap:
                parts.append(cap)
    seen, unique = set(), []
    for part in parts:
        key = part.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(part)
    return unique


def build_challenge_caption(plan: dict, items: list, birth_date: str | None = None) -> str:
    from datetime import datetime as _dt

    from .helpers import age_text, date_str, now, progress_bar

    start = _dt.strptime(date_str(plan["start_date"]), "%Y-%m-%d")
    end = _dt.strptime(date_str(plan["end_date"]), "%Y-%m-%d")
    current = _dt.strptime(now().strftime("%Y-%m-%d"), "%Y-%m-%d")

    total_days = (end - start).days + 1
    passed = (current - start).days + 1
    remaining = max(0, (end - current).days)
    percent = round((passed / total_days) * 100, 1) if total_days > 0 else 0

    body_parts = _collect_challenge_body_parts(items)

    def head(body: str) -> str:
        c = f"🔥 <b>#Challenge | Kun {passed}/{total_days}</b>\n"
        c += f"📆 {now().strftime('%d.%m.%Y')}\n"
        c += f"👤 {age_text(birth_date)}\n"
        c += f"⏳ Qoldi: {remaining} kun\n"
        c += f"📊 {progress_bar(percent)} {percent}%"
        if body:
            c += "\n\n" + escape_html(body)
        signature = bot_signature()
        if signature:
            c += "\n\n" + signature
        return c

    body_text = "\n\n".join(body_parts).strip()
    caption = head(body_text)
    # strip_tags uzunligi > 1000 bo'lsa qisqartiramiz.
    import re as _re

    if len(_re.sub(r"<[^>]+>", "", caption)) > 1000:
        caption = head("\n\n".join(body_parts)[:700])
    return caption


def send_challenge_post(chat_id, plan: dict, birth_date: str | None = None) -> None:
    try:
        items = json.loads(plan.get("items") or "null")
    except (ValueError, TypeError):
        items = []
    if not isinstance(items, list):
        items = []

    caption = build_challenge_caption(plan, items, birth_date)
    media_items = [i for i in items if i.get("type") in ("photo", "video")]
    other_items = [i for i in items if i.get("type") not in ("photo", "video", "text")]

    if media_items:
        if len(media_items) == 1:
            one = media_items[0]
            if one["type"] == "photo":
                telegram("sendPhoto", {"chat_id": chat_id, "photo": one["file_id"], "caption": caption, "parse_mode": "HTML"})
            elif one["type"] == "video":
                telegram("sendVideo", {"chat_id": chat_id, "video": one["file_id"], "caption": caption, "parse_mode": "HTML"})
        else:
            media = []
            for index, m in enumerate(media_items):
                row = {"type": m["type"], "media": m["file_id"]}
                if index == 0:
                    row["caption"] = caption
                    row["parse_mode"] = "HTML"
                media.append(row)
            telegram("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media, ensure_ascii=False)})
    else:
        send_message(chat_id, caption)

    for item in other_items:
        if item.get("type") == "audio":
            telegram("sendAudio", {"chat_id": chat_id, "audio": item["file_id"], "caption": item.get("caption", ""), "parse_mode": "HTML"})
        elif item.get("type") == "document":
            telegram("sendDocument", {"chat_id": chat_id, "document": item["file_id"], "caption": item.get("caption", ""), "parse_mode": "HTML"})
