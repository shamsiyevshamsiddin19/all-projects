"""ONEID_PROXY ishlayaptimi — parolsiz tekshiradi.

Serverda ishga tushiring:
    ONEID_PROXY=http://user:pass@host:port .venv/bin/python -m scripts.check_oneid_proxy

Hech qanday login/parol kerak emas: faqat egov.uz'ga ulanish va token_id olinishini
sinaydi. token_id kelsa — OneID oqimi shu mashinadan to'liq ishlaydi.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from core.config import settings  # noqa: E402
from lms.client import ONEID_PROXY_HOSTS, LmsClient, OneIdUnreachable  # noqa: E402


async def probe(host: str, proxy: str | None) -> str:
    kw = {"proxy": proxy} if proxy else {}
    try:
        async with httpx.AsyncClient(timeout=20, **kw) as x:
            r = await x.get(f"https://{host}/")
            return f"HTTP {r.status_code}"
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:50] or '(bo‘sh)'}"


async def main():
    proxy = settings.oneid_proxy
    masked = proxy.split("@")[-1] if proxy else "(sozlanmagan)"
    print(f"ONEID_PROXY : {masked}")
    print(f"Proksilanadi: {', '.join(ONEID_PROXY_HOSTS)}\n")

    print("1) To'g'ridan-to'g'ri (proksisiz):")
    for h in ("lms.tuit.uz",) + ONEID_PROXY_HOSTS:
        print(f"   {h:16} {await probe(h, None)}")

    if proxy:
        print("\n2) Proksi orqali:")
        for h in ONEID_PROXY_HOSTS:
            print(f"   {h:16} {await probe(h, proxy)}")

    print("\n3) To'liq OneID oqimi (LmsClient, parolsiz):")
    async with LmsClient() as c:
        try:
            tid, cid = await c._oneid_start()
            print(f"   ✅ token_id={tid}  client_id={cid}")
            print("\n   OneID shu mashinadan ISHLAYDI — botni qayta ishga tushiring.")
        except OneIdUnreachable as e:
            print(f"   ❌ {e}")
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ {type(e).__name__}: {str(e)[:90] or '(bo‘sh xabar)'}")


if __name__ == "__main__":
    asyncio.run(main())
