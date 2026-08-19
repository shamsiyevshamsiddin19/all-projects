from aiogram import Bot
from core.database import db
from core.config import ADMIN_ID

async def check_user_subscription(bot: Bot, chat_id: int):
    if chat_id == ADMIN_ID:
        return {'status': True}
    
    active = await db.get_setting('subscription_active')
    if not active or active == '0':
        return {'status': True}

    channels = await db.get_channels()
    if not channels:
        return {'status': True}

    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=chat_id)
            if member.status in ['left', 'kicked']:
                missing.append(ch['channel_id'])
        except Exception:
            missing.append(ch['channel_id'])
            
    if not missing:
        return {'status': True}
    return {'status': False, 'missing': missing}
