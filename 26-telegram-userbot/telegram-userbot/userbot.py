"""
Telegram Userbot — Telethon asosida.
Ishga tushirish:
    python userbot.py            # standart (SESSION=userbot) akkaunt
    python userbot.py acc1       # nomi acc1 bo'lgan akkaunt
"""
import asyncio
import importlib
import pathlib

from telethon import TelegramClient

import config


def load_plugins(client):
    plugins_dir = pathlib.Path(__file__).parent / "plugins"
    loaded = []
    for file in sorted(plugins_dir.glob("*.py")):
        if file.name.startswith("_"):
            continue
        module_name = f"plugins.{file.stem}"
        module = importlib.import_module(module_name)
        if hasattr(module, "register"):
            module.register(client)
        loaded.append(file.stem)
    return loaded


async def main():
    # Client'ni ishlayotgan event-loop ichida yaratamiz
    # (Python 3.14 bilan mos bo'lishi uchun).
    client = TelegramClient(
        config.SESSION_PATH,
        config.API_ID,
        config.API_HASH,
        # 24/7 ishonchli ishlash uchun:
        connection_retries=None,   # cheksiz qayta ulanish
        retry_delay=2,
        auto_reconnect=True,
        flood_sleep_threshold=120,  # kichik flood-wait larni o'zi kutadi
    )
    client.prefix = config.PREFIX

    await client.start()
    me = await client.get_me()
    plugins = load_plugins(client)
    print("=" * 40)
    print(f"Akkaunt [{config.SESSION}] ishga tushdi: {me.first_name} (@{me.username})")
    print(f"Prefiks: {config.PREFIX}")
    print(f"Yuklangan pluginlar: {', '.join(plugins) or 'yo‘q'}")
    # Saqlangan rejimlarni ko'rsatamiz (restartdan keyin tiklanadi)
    try:
        from plugins import _state as _st
        modes = []
        if _st.get("autoreply"):
            modes.append("autoreply")
        if _st.get("autoai"):
            modes.append("autoai")
        print(f"Yoqilgan rejimlar: {', '.join(modes) or 'yo‘q'}")
    except Exception:  # noqa: BLE001
        pass
    print(f"Yordam uchun: {config.PREFIX}help")
    print("=" * 40)
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUserbot to'xtatildi.")
