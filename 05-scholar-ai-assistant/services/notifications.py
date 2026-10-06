"""Admin xabarnomalari — yangi buyurtma, to'lov, balans to'ldirish."""
from __future__ import annotations
import logging
from config import settings, DOC_TYPES

logger = logging.getLogger(__name__)


async def notify_admins(bot, text: str) -> None:
    """Barcha adminlarga (ADMIN_IDS) xabar yuboradi."""
    for aid in settings.admin_ids:
        try:
            await bot.send_message(aid, text, parse_mode="HTML")
        except Exception as e:
            logger.warning("Admin xabarnoma yuborilmadi (%s): %s", aid, e)


def _uname(user) -> str:
    if getattr(user, "username", None):
        return "@" + user.username
    return f"id{getattr(user, 'id', '?')}"


async def notify_new_order(bot, user, doc_type: str, topic: str,
                           count: int, price: int, method: str) -> None:
    info = DOC_TYPES.get(doc_type, {})
    await notify_admins(
        bot,
        "🆕 <b>Yangi buyurtma</b>\n\n"
        f"👤 {_uname(user)} (<code>{getattr(user, 'id', '?')}</code>)\n"
        f"{info.get('emoji', '📄')} <b>{info.get('label', doc_type)}</b> — "
        f"{count} {info.get('unit', 'bet')}\n"
        f"📌 {topic[:80]}\n"
        f"💰 {price:,} so'm · {method}",
    )


async def notify_topup(bot, user_id: int, amount: int) -> None:
    await notify_admins(
        bot,
        "💳 <b>Hisob to'ldirildi</b>\n\n"
        f"👤 <code>{user_id}</code>\n"
        f"💰 +{amount:,} so'm",
    )
