"""Inline tugma (callback) ishlovchilari — bot.php handle_callback ekvivalenti."""

from __future__ import annotations

import json

from . import db
from .helpers import (
    build_todo_text,
    decode_task_groups,
    encode_task_groups,
    escape_html,
    flatten_task_groups,
    group_name_for_index,
    log_task_finished,
    unlog_task_finished,
    month_name_uz,
    now_str,
    reset_user_flow,
    starts_with,
    todo_keyboard,
    user_get_or_create,
    user_temp,
    user_update_step,
)
from .handlers import save_calendar_plan, save_media_plan
from .tg import (
    answer_callback,
    build_inline_day_picker,
    build_inline_hour_picker,
    build_inline_minute_picker,
    build_inline_month_picker,
    build_inline_year_picker,
    edit_message,
    keyboard_main,
    send_message,
)


def dispatch_callback(cb: dict) -> None:
    data = cb.get("data", "") or ""
    from_ = cb.get("from")
    if not from_:
        return

    user = user_get_or_create(from_)
    chat_id = cb.get("message", {}).get("chat", {}).get("id", user["chat_id"])
    message_id = cb.get("message", {}).get("message_id")
    temp = user_temp(user)
    uid = int(user["id"])

    if data == "cancel_action":
        reset_user_flow(uid)
        answer_callback(cb["id"], "Bekor qilindi")
        send_message(chat_id, "Jarayon bekor qilindi ❌\n\nAsosiy menyu ochildi.", keyboard_main())
        return

    if starts_with(data, "delete_channel:"):
        cid = int(data.split(":")[1])
        db.run("DELETE FROM user_channels WHERE id = :id AND user_id = :u", {"id": cid, "u": user["id"]})
        answer_callback(cb["id"], "O‘chirildi")
        send_message(chat_id, "Kanal yoki guruh o‘chirildi ✅", keyboard_main())
        return

    if starts_with(data, "pick_daily_plan:"):
        cid = int(data.split(":")[1])
        channel = db.one("SELECT * FROM user_channels WHERE id = :id AND user_id = :u", {"id": cid, "u": user["id"]})
        if not channel:
            answer_callback(cb["id"], "Kanal yoki guruh topilmadi")
            return
        user_update_step(uid, "waiting_media_items", {
            "plan_type": "daily_plan", "channel_row_id": cid,
            "channel_id": channel["channel_id"], "channel_name": channel["channel_name"], "items": [],
        })
        answer_callback(cb["id"], "Tanlandi")
        send_message(chat_id,
                     "📅 <b>Reja tuzish</b>\n\nEndi kontent yuboring.\n"
                     "Matn, rasm, video, audio, dokument yuborishingiz mumkin.\nTugatgach <b>✅ Tugatish</b> ni bosing.",
                     _cancel_kb())
        return

    if starts_with(data, "pick_reminder:"):
        cid = int(data.split(":")[1])
        channel = db.one("SELECT * FROM user_channels WHERE id = :id AND user_id = :u", {"id": cid, "u": user["id"]})
        if not channel:
            answer_callback(cb["id"], "Kanal yoki guruh topilmadi")
            return
        temp = {"plan_type": "reminder", "channel_row_id": cid,
                "channel_id": channel["channel_id"], "channel_name": channel["channel_name"], "items": []}
        user_update_step(uid, "waiting_reminder_date_picker", temp)
        answer_callback(cb["id"], "Tanlandi")
        edit_message(chat_id, message_id, "🎗 <b>Eslatma qo‘shish</b>\n\nEslatma uchun <b>yil</b> ni tanlang:",
                     build_inline_year_picker("reminder_date_picker"))
        return

    if starts_with(data, "pick_calendar:"):
        cid = int(data.split(":")[1])
        channel = db.one("SELECT * FROM user_channels WHERE id = :id AND user_id = :u", {"id": cid, "u": user["id"]})
        if not channel:
            answer_callback(cb["id"], "Kanal yoki guruh topilmadi")
            return
        user_update_step(uid, "waiting_calendar_type", {
            "channel_row_id": cid, "channel_id": channel["channel_id"], "channel_name": channel["channel_name"],
        })
        kb = {"inline_keyboard": [
            [{"text": "📝 Oddiy TO-DO", "callback_data": "calendar_type:todo"},
             {"text": "⏱ Super TO-DO", "callback_data": "calendar_type:super_todo"}],
            [{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}],
        ]}
        answer_callback(cb["id"], "Tanlandi")
        send_message(chat_id, "🗓 <b>Kalendar reja</b>\n\nReja turini tanlang:", kb)
        return

    if starts_with(data, "calendar_type:"):
        temp["calendar_type"] = data.split(":")[1]
        user_update_step(uid, "waiting_calendar_date_picker", temp)
        answer_callback(cb["id"], "Tanlandi")
        edit_message(chat_id, message_id, "🗓 Sana tanlash\n\nAvval <b>yil</b> ni tanlang:",
                     build_inline_year_picker("calendar_date_picker"))
        return

    if starts_with(data, "plan_kind:"):
        kind = data.split(":")[1]
        if kind == "daily":
            temp["plan_type"] = "daily_plan"
            save_media_plan(user, temp)
            answer_callback(cb["id"], "Saqlandi")
            send_message(chat_id, "📅 Oddiy reja saqlandi ✅", keyboard_main())
            return
        if kind == "challenge":
            temp["plan_type"] = "challenge"
            user_update_step(uid, "waiting_challenge_start_picker", temp)
            answer_callback(cb["id"], "Challenge")
            edit_message(chat_id, message_id, "🔥 <b>Challenge reja</b>\n\nBoshlanish uchun <b>yil</b> ni tanlang:",
                         build_inline_year_picker("challenge_start_picker"))
            return

    if starts_with(data, "pick_date_back_year:"):
        flow_key = data.split(":")[1]
        answer_callback(cb["id"], "Yil tanlash")
        edit_message(chat_id, message_id, "Sana tanlash\n\nAvval <b>yil</b> ni tanlang:", build_inline_year_picker(flow_key))
        return

    if starts_with(data, "pick_date_back_month:"):
        parts = data.split(":")
        flow_key, year = parts[1], int(parts[2])
        answer_callback(cb["id"], "Oy tanlash")
        edit_message(chat_id, message_id, f"Sana tanlash\n\n<b>{year}</b> yil uchun <b>oy</b> ni tanlang:",
                     build_inline_month_picker(flow_key, year))
        return

    if starts_with(data, "pick_year:"):
        parts = data.split(":")
        flow_key, year = parts[1], int(parts[2])
        node = temp.get(flow_key) if isinstance(temp.get(flow_key), dict) else {}
        node["year"] = year
        node.pop("month", None)
        node.pop("day", None)
        temp[flow_key] = node
        user_update_step(uid, user["step"], temp)
        answer_callback(cb["id"], "Yil tanlandi")
        edit_message(chat_id, message_id, f"📅 Tanlangan yil: <b>{year}</b>\n\nEndi <b>oy</b> ni tanlang:",
                     build_inline_month_picker(flow_key, year))
        return

    if starts_with(data, "pick_month:"):
        parts = data.split(":")
        flow_key, year, month = parts[1], int(parts[2]), int(parts[3])
        node = temp.get(flow_key) if isinstance(temp.get(flow_key), dict) else {}
        node["year"] = year
        node["month"] = month
        node.pop("day", None)
        temp[flow_key] = node
        user_update_step(uid, user["step"], temp)
        answer_callback(cb["id"], "Oy tanlandi")
        edit_message(chat_id, message_id,
                     f"📅 Tanlangan: <b>{year} {month_name_uz(month)}</b>\n\nEndi <b>kun</b> ni tanlang:",
                     build_inline_day_picker(flow_key, year, month))
        return

    if starts_with(data, "pick_day:"):
        _handle_pick_day(cb, user, temp, chat_id, message_id, data)
        return

    if starts_with(data, "pick_time_back_hour:"):
        flow_key = data.split(":")[1]
        answer_callback(cb["id"], "Soat tanlash")
        edit_message(chat_id, message_id, "Vaqt tanlash\n\nAvval <b>soat</b> ni tanlang:", build_inline_hour_picker(flow_key))
        return

    if starts_with(data, "pick_hour:"):
        parts = data.split(":")
        flow_key, hour = parts[1], int(parts[2])
        node = temp.get(flow_key) if isinstance(temp.get(flow_key), dict) else {}
        node["hour"] = hour
        node.pop("minute", None)
        temp[flow_key] = node
        user_update_step(uid, user["step"], temp)
        answer_callback(cb["id"], "Soat tanlandi")
        edit_message(chat_id, message_id, f"⏰ Tanlangan soat: <b>{hour:02d}</b>\n\nEndi <b>daqiqa</b> ni tanlang:",
                     build_inline_minute_picker(flow_key, hour))
        return

    if starts_with(data, "pick_minute:"):
        _handle_pick_minute(cb, user, temp, chat_id, message_id, data)
        return

    if starts_with(data, "delete_plan:"):
        plan_id = int(data.split(":")[1])
        db.run("UPDATE plans SET status = 'deleted', updated_at = :n WHERE id = :id AND owner_id = :u",
               {"n": now_str(), "id": plan_id, "u": user["id"]})
        answer_callback(cb["id"], "Reja o‘chirildi")
        send_message(chat_id, "Reja o‘chirildi ✅", keyboard_main())
        return

    if starts_with(data, "todo_toggle:"):
        _handle_todo_toggle(cb, chat_id, message_id, data)
        return


def _cancel_kb() -> dict:
    from .tg import keyboard_cancel

    return keyboard_cancel()


def _handle_pick_day(cb, user, temp, chat_id, message_id, data) -> None:
    parts = data.split(":")
    flow_key, year, month, day = parts[1], int(parts[2]), int(parts[3]), int(parts[4])
    date = f"{year:04d}-{month:02d}-{day:02d}"
    uid = int(user["id"])
    temp[flow_key] = {"year": year, "month": month, "day": day}

    if flow_key == "reminder_date_picker":
        temp["date"] = date
        temp["items"] = []
        user_update_step(uid, "waiting_reminder_items", temp)
        answer_callback(cb["id"], "Sana tanlandi")
        edit_message(chat_id, message_id,
                     f"📅 Sana tanlandi: <code>{date}</code>\n\n"
                     "Endi eslatma uchun kontent yuboring.\n"
                     "Matn, rasm, video, audio, dokument bo‘lishi mumkin.\nTugatgach <b>✅ Tugatish</b> ni bosing.")
        return

    if flow_key == "calendar_date_picker":
        temp["date"] = date
        temp["tasks"] = []
        user_update_step(uid, "waiting_tasks_input", temp)
        answer_callback(cb["id"], "Sana tanlandi")
        if temp.get("calendar_type", "") == "super_todo":
            edit_message(chat_id, message_id,
                         f"📅 Sana tanlandi: <code>{date}</code>\n\n"
                         "⏱ <b>Super TO-DO</b> tanlandi\n\n"
                         "Har bir vazifani quyidagi ko‘rinishda yuboring:\n<code>Vazifa | daqiqa</code>\n\n"
                         "Masalan:\n<code>Kitob o‘qish | 25</code>\n<code>Kod yozish | 40</code>\n\n"
                         "Tugatgach <b>✅ Tugatish</b> ni bosing.")
        else:
            edit_message(chat_id, message_id,
                         f"📅 Sana tanlandi: <code>{date}</code>\n\n"
                         "📝 <b>Oddiy TO-DO</b> tanlandi\n\n"
                         "Vazifalarni bitta-bittadan yoki har qatorda bittadan yuboring.\n\n"
                         "Tugatgach <b>✅ Tugatish</b> ni bosing.")
        return

    if flow_key == "challenge_start_picker":
        temp["start_date"] = date
        user_update_step(uid, "waiting_challenge_end_picker", temp)
        answer_callback(cb["id"], "Boshlanish sanasi tanlandi")
        edit_message(chat_id, message_id,
                     f"🚀 Boshlanish sanasi: <code>{date}</code>\n\nEndi challenge tugashi uchun <b>yil</b> ni tanlang:",
                     build_inline_year_picker("challenge_end_picker"))
        return

    if flow_key == "challenge_end_picker":
        start_date = temp.get("start_date")
        if start_date and date < start_date:
            answer_callback(cb["id"], "Tugash sanasi noto‘g‘ri")
            edit_message(chat_id, message_id,
                         "❌ Tugash sanasi boshlanish sanasidan kichik bo‘lishi mumkin emas.\n\n"
                         f"Boshlanish: <code>{start_date}</code>\nQaytadan tanlang:",
                         build_inline_day_picker(flow_key, year, month))
            return
        temp["end_date"] = date
        user_update_step(uid, "waiting_challenge_time_picker", temp)
        answer_callback(cb["id"], "Tugash sanasi tanlandi")
        edit_message(chat_id, message_id,
                     f"🏁 Tugash sanasi: <code>{date}</code>\n\nEndi challenge uchun <b>soat</b> ni tanlang:",
                     build_inline_hour_picker("challenge_time_picker"))
        return


def _handle_pick_minute(cb, user, temp, chat_id, message_id, data) -> None:
    parts = data.split(":")
    flow_key, hour, minute = parts[1], int(parts[2]), int(parts[3])
    time = f"{hour:02d}:{minute:02d}"
    uid = int(user["id"])
    temp[flow_key] = {"hour": hour, "minute": minute}

    if flow_key == "plan_time_picker":
        temp["time"] = time
        user_update_step(uid, "waiting_daily_plan_kind", temp)
        answer_callback(cb["id"], "Vaqt tanlandi")
        kb = {"inline_keyboard": [
            [{"text": "📅 Oddiy reja", "callback_data": "plan_kind:daily"},
             {"text": "🔥 Challenge reja", "callback_data": "plan_kind:challenge"}],
            [{"text": "❌ Bekor qilish", "callback_data": "cancel_action"}],
        ]}
        edit_message(chat_id, message_id, f"⏰ Vaqt tanlandi: <code>{time}</code>\n\nEndi reja turini tanlang:", kb)
        return

    if flow_key == "reminder_time_picker":
        temp["time"] = time
        temp["plan_type"] = "reminder"
        save_media_plan(user, temp)
        answer_callback(cb["id"], "Vaqt tanlandi")
        edit_message(chat_id, message_id,
                     "🎗 Eslatma muvaffaqiyatli saqlandi ✅\n\n"
                     f"📅 Sana: <code>{temp['date']}</code>\n⏰ Vaqt: <code>{time}</code>\n"
                     "📢 Kanal/guruh: <b>" + escape_html(temp["channel_name"]) + "</b>\n\n"
                     "Belgilangan vaqtda bot eslatmani avtomatik yuboradi.")
        send_message(chat_id, "Asosiy menyu", keyboard_main())
        return

    if flow_key == "calendar_time_picker":
        temp["time"] = time
        save_calendar_plan(user, temp)
        answer_callback(cb["id"], "Vaqt tanlandi")
        edit_message(chat_id, message_id,
                     "🗓 Kalendar reja saqlandi ✅\n\n"
                     "📢 Kanal/guruh: <b>" + escape_html(temp["channel_name"]) + "</b>\n"
                     f"📅 Sana: <code>{temp['date']}</code>\n⏰ Vaqt: <code>{time}</code>\n"
                     f"📋 Vazifalar soni: <b>{len(temp['tasks'])}</b>")
        send_message(chat_id, "Asosiy menyu", keyboard_main())
        return

    if flow_key == "challenge_time_picker":
        temp["time"] = time
        temp["plan_type"] = "challenge"
        save_media_plan(user, temp)
        answer_callback(cb["id"], "Vaqt tanlandi")
        edit_message(chat_id, message_id,
                     "🔥 Challenge reja saqlandi ✅\n\n"
                     "📢 Kanal/guruh: <b>" + escape_html(temp["channel_name"]) + "</b>\n"
                     f"⏰ Vaqt: <code>{time}</code>\n"
                     f"📅 Boshlanish: <code>{temp['start_date']}</code>\n📅 Tugash: <code>{temp['end_date']}</code>\n\n"
                     "Challenge davomida bot har kuni progress bilan post yuboradi.")
        send_message(chat_id, "Asosiy menyu", keyboard_main())
        return


def _handle_todo_toggle(cb, chat_id, message_id, data) -> None:
    parts = data.split(":")
    plan_id, index = int(parts[1]), int(parts[2])
    plan = db.one("SELECT * FROM plans WHERE id = :id AND status = 'active'", {"id": plan_id})
    if not plan:
        answer_callback(cb["id"], "Plan topilmadi")
        return
    groups = decode_task_groups(plan["tasks"])
    tasks = flatten_task_groups(groups)
    if index >= len(tasks):
        answer_callback(cb["id"], "Task topilmadi")
        return

    current = int(tasks[index].get("status", 0) or 0)
    ts = now_str()
    just_finished = False

    if plan["plan_type"] == "super_todo":
        if current == 0:
            tasks[index].update({"status": 2, "started_at": ts, "finished_at": None, "alerts": []})
            answer_text = "Boshlandi"
        elif current == 2:
            tasks[index]["status"] = 1
            if not tasks[index].get("started_at"):
                tasks[index]["started_at"] = ts
            tasks[index]["finished_at"] = ts
            answer_text = "Bajarildi"
            just_finished = True
        else:
            tasks[index].update({"status": 0, "started_at": None, "finished_at": None, "alerts": []})
            answer_text = "Qayta ochildi"
    else:
        new = 0 if current == 1 else 1
        tasks[index]["status"] = new
        answer_text = "Bajarildi" if new == 1 else "Qayta ochildi"
        just_finished = new == 1

    db.run("UPDATE plans SET tasks = :t, updated_at = :n WHERE id = :id",
           {"t": encode_task_groups(groups), "n": ts, "id": plan_id})

    if just_finished:
        log_task_finished(plan, str(tasks[index].get("text", "")), group_name_for_index(groups, index))
    elif tasks[index].get("status") == 0:
        # Qayta ochildi — bugungi jurnal yozuvi ham olib tashlanadi
        unlog_task_finished(str(tasks[index].get("text", "")))

    if plan["plan_type"] == "super_todo":
        title = "⏱ Super TO-DO"
    elif plan["plan_type"] == "daily_todo":
        title = "Har kungi rejalar"
    else:
        title = "🗓 TO-DO"

    edit_message(chat_id, message_id, build_todo_text(groups, title), todo_keyboard(plan_id, groups, plan["plan_type"]))
    answer_callback(cb["id"], answer_text)
