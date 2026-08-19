"""Uy kompyuteri orqali YouTube/Instagram yuklab olish — mijoz skripti.

Serverdagi (Hetzner) bot ba'zi foydalanuvchilar uchun YouTube/Instagram
havolalarini datacenter IP bloklangani uchun to'g'ridan-to'g'ri yuklay olmaydi.
Bu skript SHU kompyuterda (uy IP, odatda bloklanmagan) ishlaydi: serverdan
navbatdagi ishni so'raydi (pull), yt-dlp bilan yuklaydi, natijani serverga
yuboradi (upload). Server tomoni: worker/home_relay.py + web/server.py.

Ishga tushirish (shu papkada — subtitr_bot ichida):
    python tools/home_relay_client.py

Doim ishlab turishi kerak — kompyuter va shu skript yonib turmasa, o'sha
foydalanuvchi (HOME_RELAY_ADMIN_IDS, .env) yuborgan YouTube/Instagram havolasi
HOME_RELAY_GRACE_SECONDS o'tgach avtomatik oddiy server-tomon yuklashga
qaytadi (odatda blok bilan xato beradi).

To'xtatish: Ctrl+C.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests

from config import settings
from worker.download import download_video

# Server manzili — tunnel URL har restartda o'zgaradi, shuning uchun
# TO'G'RIDAN-TO'G'RI server IP:8080 ishlatiladi (barqaror, ufw'da ochilgan).
SERVER = os.getenv("HOME_RELAY_SERVER", "http://178.104.25.218:8080")
POLL_INTERVAL = 3.0

# pythonw (oynasiz) rejimda konsol yo'q — loglarni faylga yozamiz (nosozlikni
# keyin ko'rish uchun). Fayl juda kattalashmasin uchun 1MB dan oshsa qisqaradi.
_LOG_PATH = os.path.join(os.path.dirname(__file__), "home_relay.log")


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        if os.path.exists(_LOG_PATH) and os.path.getsize(_LOG_PATH) > 1_000_000:
            with open(_LOG_PATH, "r+", encoding="utf-8") as f:
                data = f.read()[-200_000:]
                f.seek(0)
                f.write(data)
                f.truncate()
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def main() -> None:
    secret = settings.home_relay_secret
    if not secret:
        _log("XATO: .env da HOME_RELAY_SECRET yo'q. Server bilan bir xil qiymat kerak.")
        return
    _log(f"Uy relay ishga tushdi. Server: {SERVER}")
    while True:
        try:
            r = requests.get(
                f"{SERVER}/internal/home/pull", params={"secret": secret}, timeout=15
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            _log(f"Serverga ulanib bo'lmadi ({exc}) — {POLL_INTERVAL:.0f}s kutib qayta uriniladi")
            time.sleep(POLL_INTERVAL)
            continue

        job_id = data.get("job_id")
        if not job_id:
            time.sleep(POLL_INTERVAL)
            continue

        url = data["url"]
        _log(f"Yangi ish: {job_id} -> {url}")
        tmp_path = os.path.join(os.path.dirname(__file__), f"_relay_{job_id}.mp4")
        try:
            download_video(url, tmp_path)
            size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
            _log(f"Yuklandi ({size_mb:.1f} MB) — serverga yuborilmoqda...")
            with open(tmp_path, "rb") as f:
                resp = requests.post(
                    f"{SERVER}/internal/home/upload",
                    params={"secret": secret},
                    data={"job_id": job_id},
                    files={"file": (f"{job_id}.mp4", f, "video/mp4")},
                    timeout=1800,
                )
            resp.raise_for_status()
            _log(f"Yuborildi: {job_id} ✅")
        except Exception as exc:
            _log(f"XATO ({job_id}): {exc}")
            try:
                requests.post(
                    f"{SERVER}/internal/home/fail",
                    params={"secret": secret},
                    json={"job_id": job_id, "error": str(exc)},
                    timeout=15,
                )
            except Exception:
                pass
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")
