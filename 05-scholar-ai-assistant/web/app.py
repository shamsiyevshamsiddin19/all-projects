"""aiohttp web server — admin panel + click webhook."""
from __future__ import annotations
from aiohttp import web
from web.admin import setup_admin_routes
from web.click_webhook import setup_click_routes
from config import settings


def create_app(bot=None) -> web.Application:
    app = web.Application()
    setup_admin_routes(app, bot)
    setup_click_routes(app)
    return app


async def run_web(bot=None):
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    return runner
