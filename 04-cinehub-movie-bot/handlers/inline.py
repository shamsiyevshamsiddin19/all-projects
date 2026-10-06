"""Inline rejim: istalgan chatda @bot orqali kino/serial qidirish."""
from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

import config
import db
import utils

router = Router()


@router.inline_query()
async def inline_search(iq: InlineQuery):
    query = (iq.query or "").strip()

    if not query:
        # bo'sh so'rov — eng ommabop kinolar
        rows = await db.fetch(
            """(SELECT code, name, views, 'movie' AS type FROM movies ORDER BY views DESC LIMIT 15)
               UNION ALL
               (SELECT code, name, views, 'series' AS type FROM series ORDER BY views DESC LIMIT 10)
               ORDER BY views DESC LIMIT 25"""
        )
    else:
        like = f"%{utils.normalize_search_text(query)}%"
        rows = await db.fetch(
            """(SELECT code, name, views, 'movie' AS type FROM movies WHERE lower(name) LIKE $1 LIMIT 25)
               UNION ALL
               (SELECT code, name, views, 'series' AS type FROM series WHERE lower(name) LIKE $1 LIMIT 25)
               LIMIT 40""",
            like,
        )

    results = []
    for r in rows:
        is_series = r["type"] == "series"
        icon = "📺" if is_series else "🎬"
        kind = "Serial" if is_series else "Kino"
        link = utils.deep_link(r["code"])
        text = (
            f"{icon} <b>{utils.h(r['name'])}</b>\n"
            f"🆔 Kod: <code>{r['code']}</code>\n"
            f"👁 {r['views']} marta ko'rilgan\n\n"
            f"▶️ Ko'rish uchun tugmani bosing 👇"
        )
        results.append(
            InlineQueryResultArticle(
                id=f"{r['type']}_{r['code']}",
                title=f"{icon} {r['name']}",
                description=f"{kind} • Kod: {r['code']} • 👁 {r['views']}",
                input_message_content=InputTextMessageContent(
                    message_text=text, parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text=f"▶️ {kind}ni ochish", url=link)]]
                ),
            )
        )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id="notfound",
                title="🤷‍♂️ Hech narsa topilmadi",
                description="Boshqa nom bilan urinib ko'ring",
                input_message_content=InputTextMessageContent(
                    message_text=f"🔎 Kino izlash uchun botga o'ting: @{config.BOT_USERNAME}"
                ),
            )
        )

    await iq.answer(results, cache_time=5, is_personal=True)
