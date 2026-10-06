#!/usr/bin/env python3
"""Webhook boshqaruvi (set_webhook.php o'rniga).

  python set_webhook.py set https://domeningiz.uz/boost/webhook [SECRET]
  python set_webhook.py info
  python set_webhook.py delete
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings  # noqa: E402
from app.tg import telegram  # noqa: E402


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    if cmd == "set":
        if len(sys.argv) < 3:
            print("Xato: webhook URL kiriting.")
            sys.exit(1)
        url = sys.argv[2]
        params = {"url": url, "drop_pending_updates": "true"}
        secret = sys.argv[3] if len(sys.argv) > 3 else settings.WEBHOOK_SECRET
        if secret:
            params["secret_token"] = secret
        res = telegram("setWebhook", params)
    elif cmd == "delete":
        res = telegram("deleteWebhook", {"drop_pending_updates": "true"})
    else:
        res = telegram("getWebhookInfo")

    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
