"""Bot mantiqi — xabar va callback ishlovchilari (bot.php ekvivalenti)."""

from __future__ import annotations

import json
import logging

from . import db
from .helpers import (
    build_todo_text,
    escape_html,
    month_name_uz,
    next_datetime_for_daily,
    now_str,
    parse_channel_input,
    reset_user_flow,
    starts_with,
    todo_keyboard,
    user_get_or_create,
    user_temp,
    user_update_step,
    valid_date,
)
from .tg import (
    CANCEL_TEXT,
    FINISH_TEXT,
    MINIAPP_BUTTON_TEXT,
    answer_callback,
    bot_is_admin,
    build_inline_day_picker,
    build_inline_hour_picker,
    build_inline_minute_picker,
    build_inline_month_picker,
    build_inline_year_picker,
    edit_message,
    extract_media_item,
    get_chat_info_multi,
    inline_channels,
    is_supported_target_chat,
    keyboard_cancel,
    keyboard_main,
    miniapp_inline_keyboard,
    only_cancel_keyboard,
    send_message,
    target_chat_type_label,
)

logger = logging.getLogger("boostday")


def handle_update(update: dict) -> None:
    try:
        if "callback_query" in update:
            handle_callback(update["callback_query"])
            return
        if "message" not in update:
            return
        message = update["message"]
        from_ = message.get("from")
        if not from_:
            return

        user = user_get_or_create(from_)
        chat_id = user["chat_id"]
        text = (message.get("text") or "").strip()

        if text == "/start":
            if not user.get("birth_date"):
                user_update_step(int(user["id"]), "waiting_birth_date", {})
                send_message(
                    chat_id,
                    f"Assalomu alaykum, <b>{escape_html(user['first_name'])}</b> 👋\n\n"
                    "Bu bot sizga kanal yoki guruh uchun reja, eslatma, challenge va TO-DO tizimini yuritishga yordam beradi.\n\n"
                    "Avval tug‘ilgan kuningizni yuboring.\n"
                    "<b>Format:</b> <code>YYYY-MM-DD</code>\n"
                    "Masalan: <code>2007-03-25</code>",
                    only_cancel_keyboard(),
                )
            else:
                reset_user_flow(int(user["id"]))
                send_message(
                    chat_id,
                    "Asosiy menyu ochildi ✅\n\n"
                    "🚀 <b>Mini App</b> orqali rejalaringizni tez va qulay boshqaring — "
                    f"pastdagi <b>{escape_html(MINIAPP_BUTTON_TEXT)}</b> tugmasini "
                    "yoki input yonidagi ☰ menyu tugmasini bosing.",
                    keyboard_main(),
                )
            return

        if text == CANCEL_TEXT:
            reset_user_flow(int(user["id"]))
            send_message(chat_id, "Jarayon bekor qilindi ❌\n\nAsosiy menyu ochildi.", keyboard_main())
            return

        if not user.get("birth_date"):
            handle_birth_date(user, message)
            return

        menu = {
            MINIAPP_BUTTON_TEXT: lambda: send_message(
                chat_id,
                "🚀 <b>Mini App</b> — rejalaringizni tez va qulay boshqaring.\n\nPastdagi tugmani bosing 👇",
                miniapp_inline_keyboard(),
            ),
            "📢 Kanal ulash": lambda: start_add_channel(user),
            "📢 Kanallarim": lambda: show_user_channels(user),
            "📅 Reja tuzish": lambda: start_plan_select_channel(user, "daily_plan"),
            "🎗 Eslatma qo‘shish": lambda: start_plan_select_channel(user, "reminder"),
            "🗓 Kalendar reja": lambda: start_plan_select_channel(user, "calendar"),
            "📂 Mening rejalarim": lambda: show_my_plans(user),
        }
        if text in menu:
            menu[text]()
            return

        handle_step_message(user, message)
    except Exception as e:  # noqa: BLE001
        logger.exception("BOT_FATAL: %s", e)


def handle_birth_date(user: dict, message: dict) -> None:
    chat_id = user["chat_id"]
    text = (message.get("text") or "").strip()
    if not valid_date(text):
        send_message(
            chat_id,
            "Sana noto‘g‘ri kiritildi ⚠️\n\n"
            "Tug‘ilgan kuningizni quyidagi formatda yuboring:\n"
            "<code>YYYY-MM-DD</code>\n\n"
            "Masalan: <code>2007-03-25</code>",
            only_cancel_keyboard(),
        )
        return
    db.run(
        "UPDATE users SET birth_date = :b, step = NULL, temp_data = NULL, updated_at = :n WHERE id = :id",
        {"b": text, "n": now_str(), "id": user["id"]},
    )
    send_message(
        chat_id,
        f"Tug‘ilgan kun saqlandi ✅\n\n📅 Sana: <b>{text}</b>\n\nAsosiy menyu ochildi.",
        keyboard_main(),
    )


def start_add_channel(user: dict) -> None:
    user_update_step(int(user["id"]), "waiting_channel_input", {})
    send_message(
        user["chat_id"],
        "📢 <b>Kanal yoki guruh ulash</b>\n\n"
        "Quyidagilardan birini yuboring:\n"
        "• <code>@kanal_nomi</code>\n"
        "• <code>https://t.me/kanal_nomi</code>\n"
        "• forward qilingan xabar\n"
        "• channel ID\n\n"
        "Muhim: bot o‘sha kanal yoki guruhda <b>admin</b> bo‘lishi kerak.",
        only_cancel_keyboard(),
    )


def show_user_channels(user: dict) -> None:
    rows = db.all_("SELECT * FROM user_channels WHERE user_id = :u ORDER BY id DESC", {"u": user["id"]})
    if not rows:
        send_message(
            user["chat_id"],
            "Sizda hali ulangan kanal yoki guruh yo‘q 📭\n\nAvval <b>📢 Kanal ulash</b> bo‘limidan foydalaning.",
            keyboard_main(),
        )
        return
    text = "<b>📢 Ulangan kanal va guruhlar:</b>\n\n"
    kb = {"inline_keyboard": []}
    for i, r in enumerate(rows):
        text += f"{i + 1}. {escape_html(r['channel_name'])}\n🆔 <code>{r['channel_id']}</code>\n\n"
        kb["inline_keyboard"].append([{
            "text": "🗑 O‘chirish: " + str(r["channel_name"])[:30],
            "callback_data": f"delete_channel:{r['id']}",
        }])
    send_message(user["chat_id"], text, kb)


def start_plan_select_channel(user: dict, mode: str) -> None:
    channels = db.all_("SELECT * FROM user_channels WHERE user_id = :u ORDER BY id DESC", {"u": user["id"]})
    if not channels:
        send_message(
            user["chat_id"],
            "Avval kanal yoki guruh ulab oling ⚠️\n\nBuning uchun <b>📢 Kanal ulash</b> bo‘limidan foydalaning.",
            keyboard_main(),
        )
        return
    user_update_step(int(user["id"]), f"select_channel_for_{mode}", {"mode": mode})
    send_message(user["chat_id"], "Kerakli kanal yoki guruhni tanlang 👇", inline_channels(channels, f"pick_{mode}"))


def handle_step_message(user: dict, message: dict) -> None:
    step = user.get("step")
    chat_id = user["chat_id"]
    temp = user_temp(user)
    text = (message.get("text") or "").strip()

    if step == "waiting_channel_input":
        _handle_channel_input(user, message, chat_id)
        return

    if step in ("waiting_media_items", "waiting_reminder_items"):
        is_reminder = step == "waiting_reminder_items"
        if text == FINISH_TEXT:
            if not temp.get("items"):
                send_message(chat_id, "Hech qanday kontent yuborilmadi ⚠️", keyboard_cancel())
                return
            next_step = "waiting_reminder_time_picker" if is_reminder else "waiting_plan_time_picker"
            picker_key = "reminder_time_picker" if is_reminder else "plan_time_picker"
            label = "eslatma" if is_reminder else "chiqish"
            user_update_step(int(user["id"]), next_step, temp)
            send_message(chat_id, f"Kontent saqlandi ✅\n\nEndi {label} <b>vaqt</b> ini tanlang:",
                         build_inline_hour_picker(picker_key))
            return
        item = extract_media_item(message)
        if not item:
            send_message(chat_id, "Faqat matn yoki media yuboring ⚠️\n\nTugatgach <b>✅ Tugatish</b> ni bosing.", keyboard_cancel())
            return
        temp.setdefault("items", []).append(item)
        user_update_step(int(user["id"]), step, temp)
        send_message(
            chat_id,
            "🖼 Album elementi qabul qilindi.\n\nYana yuborishingiz mumkin yoki <b>✅ Tugatish</b> ni bosing."
            if item.get("media_group_id")
            else "Kontent qo‘shildi ✅\n\nYana yuborishingiz mumkin yoki <b>✅ Tugatish</b> ni bosing.",
            keyboard_cancel(),
        )
        return

    if step == "waiting_tasks_input":
        if text == FINISH_TEXT:
            if not temp.get("tasks"):
                send_message(chat_id, "Vazifalar kiritilmagan ⚠️", keyboard_cancel())
                return
            user_update_step(int(user["id"]), "waiting_calendar_time_picker", temp)
            send_message(chat_id, "Vazifalar saqlandi ✅\n\nEndi reja chiqish <b>vaqt</b> ini tanlang:",
                         build_inline_hour_picker("calendar_time_picker"))
            return
        for line in text.splitlines():
            line = line.strip()
            if line == "":
                continue
            if temp.get("calendar_type", "") == "super_todo":
                if "|" not in line:
                    send_message(chat_id, "Super TO-DO format xato ⚠️\n\nTo‘g‘ri format:\n<code>Vazifa | daqiqa</code>", keyboard_cancel())
                    return
                parts = line.split("|", 1)
                task_text = parts[0].strip()
                duration = parts[1].strip()
                if task_text == "" or not duration.isdigit():
                    send_message(chat_id, "Super TO-DO format xato ⚠️\n\nTo‘g‘ri format:\n<code>Vazifa | daqiqa</code>", keyboard_cancel())
                    return
                temp.setdefault("tasks", []).append({
                    "text": task_text, "duration": int(duration), "status": 0,
                    "started_at": None, "finished_at": None, "alerts": [],
                })
            else:
                temp.setdefault("tasks", []).append({"text": line, "status": 0})
        user_update_step(int(user["id"]), "waiting_tasks_input", temp)
        send_message(chat_id, "Vazifa(lar) qo‘shildi ✅\n\nYana yuborishingiz mumkin yoki <b>✅ Tugatish</b> ni bosing.", keyboard_cancel())
        return

    send_message(chat_id, "Bu bosqichda matn kiritish emas, bot yuborgan tugmalardan foydalanish kerak ℹ️", only_cancel_keyboard())


def _handle_channel_input(user: dict, message: dict, chat_id) -> None:
    parsed = parse_channel_input(message)
    if not parsed:
        send_message(
            chat_id,
            "Kanal yoki guruh formati noto‘g‘ri ⚠️\n\n"
            "Quyidagilardan birini yuboring:\n"
            "• <code>@kanal_nomi</code>\n• <code>https://t.me/kanal_nomi</code>\n"
            "• forward qilingan xabar\n• channel ID",
            only_cancel_keyboard(),
        )
        return
    candidates = parsed.get("channel_candidates") or [parsed["channel_id"]]
    chat_info = get_chat_info_multi(candidates)
    if not chat_info:
        send_message(chat_id, "Kanal yoki guruh topilmadi ❌\n\nBotni avval kanal yoki guruhga admin qiling va qayta urinib ko‘ring.", only_cancel_keyboard())
        return
    if not is_supported_target_chat(chat_info):
        send_message(chat_id, "Faqat kanal yoki guruhni ulash mumkin ❌\n\nTopilgan chat turi: <b>" + escape_html(target_chat_type_label(chat_info)) + "</b>.", only_cancel_keyboard())
        return
    channel_id = str(chat_info["id"])
    channel_name = chat_info.get("title") or parsed.get("channel_name") or "Noma’lum kanal"
    channel_username = ("@" + chat_info["username"]) if chat_info.get("username") else parsed.get("channel_username")

    if not bot_is_admin(channel_id):
        send_message(chat_id, "Bot bu kanal yoki guruhda admin emas ❌\n\nAvval botni administrator qiling.", only_cancel_keyboard())
        return

    existing = db.one("SELECT * FROM user_channels WHERE user_id = :u AND channel_id = :c", {"u": user["id"], "c": channel_id})
    if existing:
        db.run("UPDATE user_channels SET channel_name = :n, channel_username = :un, created_at = :ts WHERE id = :id",
               {"n": channel_name, "un": channel_username, "ts": now_str(), "id": existing["id"]})
    else:
        db.run("INSERT INTO user_channels (user_id, channel_id, channel_name, channel_username, created_at) VALUES (:u, :c, :n, :un, :ts)",
               {"u": user["id"], "c": channel_id, "n": channel_name, "un": channel_username, "ts": now_str()})

    reset_user_flow(int(user["id"]))
    send_message(chat_id, "✅ Kanal/guruh muvaffaqiyatli ulandi\n\n📌 <b>" + escape_html(channel_name) + f"</b>\n🆔 <code>{channel_id}</code>", keyboard_main())


def save_media_plan(user: dict, temp: dict) -> None:
    ts = now_str()
    plan_type = temp["plan_type"]
    next_run_at = None
    if plan_type == "daily_plan":
        next_run_at = next_datetime_for_daily(temp["time"])
    elif plan_type == "reminder":
        next_run_at = f"{temp['date']} {temp['time']}:00"
    elif plan_type == "challenge":
        from .helpers import today_str

        base = max(today_str(), temp["start_date"])
        next_run_at = f"{base} {temp['time']}:00"

    db.run(
        "INSERT INTO plans (owner_id, channel_id, channel_name, plan_type, items, time, date, start_date, end_date, "
        "next_run_at, created_at, updated_at) VALUES "
        "(:owner, :cid, :cname, :pt, :items, :time, :date, :sd, :ed, :nra, :ts, :ts)",
        {
            "owner": user["id"], "cid": temp["channel_id"], "cname": temp["channel_name"], "pt": plan_type,
            "items": json.dumps(temp["items"], ensure_ascii=False),
            "time": temp.get("time"), "date": temp.get("date"),
            "sd": temp.get("start_date"), "ed": temp.get("end_date"), "nra": next_run_at, "ts": ts,
        },
    )
    reset_user_flow(int(user["id"]))


def save_calendar_plan(user: dict, temp: dict) -> None:
    ts = now_str()
    db.run(
        "INSERT INTO plans (owner_id, channel_id, channel_name, plan_type, tasks, date, time, next_run_at, "
        "created_at, updated_at) VALUES (:owner, :cid, :cname, :pt, :tasks, :date, :time, :nra, :ts, :ts)",
        {
            "owner": user["id"], "cid": temp["channel_id"], "cname": temp["channel_name"],
            "pt": temp["calendar_type"], "tasks": json.dumps(temp["tasks"], ensure_ascii=False),
            "date": temp["date"], "time": temp["time"], "nra": f"{temp['date']} {temp['time']}:00", "ts": ts,
        },
    )
    reset_user_flow(int(user["id"]))


def show_my_plans(user: dict) -> None:
    rows = db.all_("SELECT * FROM plans WHERE owner_id = :u AND status = 'active' ORDER BY id DESC LIMIT 30", {"u": user["id"]})
    if not rows:
        send_message(user["chat_id"], "Hozircha saqlangan rejalar yo‘q 📂", keyboard_main())
        return
    text = "<b>📂 Mening rejalarim</b>\n\n"
    kb = {"inline_keyboard": []}
    labels = {
        "todo": "Oddiy TO-DO", "super_todo": "Super TO-DO", "daily_plan": "Oddiy reja",
        "challenge": "Challenge reja", "reminder": "Eslatma", "daily_todo": "Har kungi reja",
    }
    for row in rows:
        preview = ""
        if row.get("items"):
            try:
                items = json.loads(row["items"])
            except (ValueError, TypeError):
                items = []
            preview = f"📦 Kontentlar: {len(items) if isinstance(items, list) else 0} ta"
        if row.get("tasks"):
            try:
                tasks = json.loads(row["tasks"])
            except (ValueError, TypeError):
                tasks = []
            preview = f"📋 Vazifalar: {len(tasks) if isinstance(tasks, list) else 0} ta"
        type_label = labels.get(row["plan_type"], row["plan_type"])
        text += f"🆔 ID: <code>{row['id']}</code>\n📌 Turi: <b>{type_label}</b>\n"
        text += "📢 Kanal/guruh: " + escape_html(row["channel_name"] or row["channel_id"]) + "\n"
        if row.get("date"):
            text += f"📅 Sana: <code>{row['date']}</code>\n"
        if row.get("time"):
            text += f"⏰ Vaqt: <code>{row['time']}</code>\n"
        if row.get("start_date"):
            text += f"🚀 Boshlanish: <code>{row['start_date']}</code>\n"
        if row.get("end_date"):
            text += f"🏁 Tugash: <code>{row['end_date']}</code>\n"
        if preview:
            text += preview + "\n"
        text += "\n"
        kb["inline_keyboard"].append([{"text": f"🗑 Rejani o‘chirish #{row['id']}", "callback_data": f"delete_plan:{row['id']}"}])
    send_message(user["chat_id"], text, kb)


def handle_callback(cb: dict) -> None:
    from .callbacks import dispatch_callback

    dispatch_callback(cb)
