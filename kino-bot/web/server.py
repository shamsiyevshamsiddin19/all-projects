"""Web-admin serverni aiogram bilan bir loopda ishga tushirish."""
import logging

from aiohttp import web

import config
from .admin import setup_admin_routes

logger = logging.getLogger(__name__)


async def start_web(bot=None):
    app = web.Application()
    setup_admin_routes(app, bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=config.WEB_HOST, port=config.WEB_PORT)
    await site.start()
    logger.info("Web-admin tayyor: http://%s:%s/admin", config.WEB_HOST, config.WEB_PORT)
    return runner
