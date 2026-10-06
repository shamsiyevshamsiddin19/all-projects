#!/usr/bin/env python3
"""Rejalashtirilgan vazifalarni bajaradi (cron.php o'rniga). Har daqiqada ishga tushiring.

Crontab:
  * * * * * /opt/yordamchi/Boostdaybot/bot_py/.venv/bin/python /opt/yordamchi/Boostdaybot/bot_py/run_cron.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import db  # noqa: E402
from app.scheduler import run_all  # noqa: E402

if __name__ == "__main__":
    try:
        db.migrate()
        run_all()
        print("CRON_OK")
    except Exception as e:  # noqa: BLE001
        print(f"CRON_ERROR: {e}")
        sys.exit(1)
