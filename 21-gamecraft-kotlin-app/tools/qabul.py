#!/usr/bin/env python3
"""Telefondan kelgan tashxis kadrlarini qabul qiladi.

Telefonda jurnalga kirish imkoni yo'q, shuning uchun ilova ko'rgan xom kadrni
o'zi shu yerga yuboradi. Kadr kelishi bilan uni o'sha tanish quvuridan
o'tkazib ko'rsa bo'ladi - taxmin qilish shart emas.

    python3 tools/qabul.py [port] [papka]
"""
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
PAPKA = sys.argv[2] if len(sys.argv) > 2 else "data/telefon"


class Qabul(BaseHTTPRequestHandler):
    def do_POST(self):
        nom = self.headers.get("X-Nom", f"kadr-{int(time.time())}")
        nom = os.path.basename(nom)          # yo'l bilan o'ynashga yo'l qo'ymaymiz
        uzunlik = int(self.headers.get("Content-Length", 0))
        malumot = self.rfile.read(uzunlik)
        os.makedirs(PAPKA, exist_ok=True)
        yol = os.path.join(PAPKA, nom)
        with open(yol, "wb") as f:
            f.write(malumot)
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")
        print(f"QABUL: {nom} ({len(malumot)} bayt)", flush=True)

    def do_GET(self):
        # Ilova serverni shu bilan topadi
        self.send_response(200)
        self.send_header("Content-Length", "4")
        self.end_headers()
        self.wfile.write(b"bor\n")

    def log_message(self, *a):
        pass          # o'z xabarlarimiz yetarli


if __name__ == "__main__":
    os.makedirs(PAPKA, exist_ok=True)
    print(f"kutilyapti: 0.0.0.0:{PORT} -> {PAPKA}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Qabul).serve_forever()
