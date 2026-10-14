"""Pluginlar uchun umumiy yordamchilar."""
import re

from telethon import events

import config

# Har bir buyruq {nom: tavsif} shaklida shu yerga yoziladi (help uchun)
COMMANDS = {}


def command(pattern, description=""):
    """
    Faqat o'zingiz (outgoing) yozgan buyruqlarni tinglaydigan dekorator.

    pattern: buyruq nomi, masalan "ping" yoki "purge"
    description: help ro'yxatida ko'rinadigan izoh
    """
    name = pattern.split()[0]
    COMMANDS[name] = description

    def decorator(func):
        prefix = re.escape(config.PREFIX)
        # .ping  yoki  .ping <arg>
        regex = rf"^{prefix}{pattern}(?: |$)(.*)"
        func._event = events.NewMessage(outgoing=True, pattern=regex)
        return func

    return decorator


def register_all(client, module):
    """Moduldagi barcha @command bilan belgilangan funksiyalarni ro'yxatga oladi."""
    for obj in vars(module).values():
        if callable(obj) and hasattr(obj, "_event"):
            client.add_event_handler(obj, obj._event)
