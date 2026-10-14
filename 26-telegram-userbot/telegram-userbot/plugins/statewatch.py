"""Sozlamalar faylini (data/state_<acc>.json) jonli kuzatadi.

Web panel yoki tashqi o'zgarish bo'lsa, botning ichki holatini (STATE) diskdan
qayta o'qib yangilaydi — qayta ishga tushirish shart emas.
"""
import asyncio

from . import _state as state
from . import autoai, autodraft, autoread, autoreply
from ._helpers import register_all

WATCH_INTERVAL = 5  # soniya


def _apply(d):
    autoreply.STATE["enabled"] = bool(d.get("autoreply", False))
    autodraft.STATE["enabled"] = bool(d.get("autodraft", False))
    autoai.STATE["enabled"] = bool(d.get("autoai", False))

    kinds = d.get("autoread_kinds")
    autoread.KINDS.clear()
    if kinds is not None:
        autoread.KINDS.update(kinds)
    elif d.get("autoread"):
        autoread.KINDS.update(autoread.ALL_KINDS)


async def _watch():
    last = None
    while True:
        await asyncio.sleep(WATCH_INTERVAL)
        try:
            d = state.load()
            if d != last:
                _apply(d)
                last = d
        except Exception as e:  # noqa: BLE001
            print(f"[statewatch] xato: {e}", flush=True)


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
    asyncio.create_task(_watch())
