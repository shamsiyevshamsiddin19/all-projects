#!/usr/bin/env python3
"""LOKAL ishga tushirish: Telegram long-polling orqali botni yuritadi.

Webhook/tunnel shart emas. Ishlashi:
  1. Webhookni o'chiradi (polling va webhook bir vaqtda ishlamaydi).
  2. getUpdates tsiklida yangilanishlarni oladi va handle_update ga uzatadi
     (webhook bilan bir xil kod yo'li).

  python run_polling.py

Ctrl+C bilan to'xtatiladi. DIQQAT: bu ishlagan vaqtda bot tokeni shu mashinaga
"band" bo'ladi — boshqa joydagi (webhook yoki polling) nusxa xabar olmaydi.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import db  # noqa: E402
from app.config import settings  # noqa: E402
from app.handlers import handle_update  # noqa: E402
from app.tg import telegram  # noqa: E402

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("boostday.poll")


def main() -> None:
    if not settings.BOT_TOKEN:
        print("BOT_TOKEN topilmadi (.env ni tekshiring).")
        return

    try:
        db.migrate()
    except Exception:  # noqa: BLE001
        logger.exception("Schema init xatosi (davom etamiz)")

    # Webhookni olib tashlab, polling'ga o'tamiz (drop_pending_updates=false — navbatdagilar ishlansin).
    telegram("deleteWebhook", {"drop_pending_updates": "false"})
    logger.info("Polling boshlandi. Bot: @%s (Ctrl+C to'xtatadi)", settings.BOT_USERNAME)

    offset: int | None = None
    while True:
        params: dict = {"timeout": 20}
        if offset is not None:
            params["offset"] = offset
        resp = telegram("getUpdates", params)
        if not resp or not resp.get("ok"):
            time.sleep(2)
            continue
        for update in resp.get("result", []):
            offset = int(update["update_id"]) + 1
            try:
                handle_update(update)
            except Exception:  # noqa: BLE001
                logger.exception("UPDATE_HANDLE_ERROR update_id=%s", update.get("update_id"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPolling to'xtatildi.")
