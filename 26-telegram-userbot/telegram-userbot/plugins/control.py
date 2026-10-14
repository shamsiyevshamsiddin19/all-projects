"""Boshqaruv paneli — barcha rejimlarni bitta joydan yoqib/o'chirish.

Buyruqlar:
  .bot            — panel: qaysi rejim yoqilganini ko'rsatadi
  .bot on         — ishchi rejim: avto-javob + avto-o'qish YOQILADI
  .bot off        — hamma rejim O'CHADI
  .bot autoreply  — avto-javobni yoqib/o'chiradi (toggle)
  .bot autoread   — avto-o'qishni (hammasi) yoqib/o'chiradi
  .bot autoai     — yarim-avtomatik taklifni yoqib/o'chiradi
"""
import config

from . import _state as state
from . import autoai, autodraft, autoread, autoreply
from ._helpers import command, register_all


def _panel_link():
    if config.PANEL_URL and config.PANEL_TOKEN:
        return f"{config.PANEL_URL}/?token={config.PANEL_TOKEN}"
    return None

LABELS = {
    "autoreply": "🤖 Avto-javob",
    "autodraft": "✍️ Qoralama (shaxsiy)",
    "autoread": "👁 Avto-o'qish",
    "autoai": "📝 Yarim-avto taklif",
}


def _get(name):
    if name == "autoreply":
        return autoreply.STATE.get("enabled")
    if name == "autodraft":
        return autodraft.STATE.get("enabled")
    if name == "autoai":
        return autoai.STATE.get("enabled")
    if name == "autoread":
        return bool(autoread.KINDS)
    return False


def _set(name, value):
    if name == "autoreply":
        autoreply.STATE["enabled"] = value
        state.set("autoreply", value)
    elif name == "autodraft":
        autodraft.STATE["enabled"] = value
        state.set("autodraft", value)
    elif name == "autoai":
        autoai.STATE["enabled"] = value
        state.set("autoai", value)
        if not value:
            autoai.PENDING.clear()
    elif name == "autoread":
        if value:
            autoread.KINDS.update(autoread.ALL_KINDS)
        else:
            autoread.KINDS.clear()
        autoread._persist()


def _panel(with_link=True):
    lines = []
    link = _panel_link()
    if with_link and link:
        lines.append(f"🌐 **Sozlash paneli:**\n{link}\n")
    lines.append("**🎛 Rejimlar**")
    for name, label in LABELS.items():
        on = _get(name)
        lines.append(f"{'🟢' if on else '⚪️'} {label} — `{name}`")
    lines.append("\n`.bot on` — ishchi rejim  |  `.bot off` — hammasi o‘chadi")
    return "\n".join(lines)


@command("bot", "Boshqaruv paneli — rejimlarni yoqib/o'chirish (.bot on/off)")
async def bot_cmd(event):
    arg = event.pattern_match.group(1).strip().lower()
    if arg == "on":
        _set("autoreply", True)
        _set("autoread", True)
        await event.edit("🟢 **Ishchi rejim YOQILDI** (avto-javob + avto-o'qish)\n\n" + _panel())
    elif arg == "off":
        for name in LABELS:
            _set(name, False)
        await event.edit("⛔ **Hamma rejim O'CHIRILDI**\n\n" + _panel())
    elif arg in LABELS:
        new_value = not _get(arg)
        _set(arg, new_value)
        holat = "🟢 yoqildi" if new_value else "⚪️ o‘chirildi"
        await event.edit(f"{LABELS[arg]}: {holat}\n\n" + _panel())
    else:
        await event.edit(_panel())


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
