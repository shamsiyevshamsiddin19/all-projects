"""Barcha buyruqlar ro'yxati."""
import config

from ._helpers import COMMANDS, command, register_all


@command("help", "Barcha buyruqlarni ko'rsatadi")
async def help_cmd(event):
    p = config.PREFIX
    lines = ["**📋 Mavjud buyruqlar:**\n"]
    for name, desc in sorted(COMMANDS.items()):
        lines.append(f"• `{p}{name}` — {desc}")
    await event.edit("\n".join(lines))


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
