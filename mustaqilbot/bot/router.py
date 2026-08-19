from aiogram import Router
from bot.handlers import start, order, payment, referral, profile, inline

def build_router() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(order.router)
    root.include_router(payment.router)
    root.include_router(referral.router)
    root.include_router(profile.router)
    root.include_router(inline.router)
    return root
