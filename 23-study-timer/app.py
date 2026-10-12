#!/usr/bin/env python3
"""
Zenith Study Timer — mahalliy server va JSON ma'lumot ombori.

Xavfsizlik qarorlari:
  * Standart holatda FAQAT 127.0.0.1 ga bog'lanadi — umumiy Wi-Fi'da loyiha fayllari
    va shaxsiy statistika tashqariga ochilmaydi (`--host` bilan ataylab o'zgartiriladi).
  * `/api/data` da CORS yo'q va cross-site so'rovlar rad etiladi — brauzerdagi
    boshqa sayt localhost'ga yozib ketmasligi uchun.
  * Body hajmi cheklangan, buzilgan `Content-Length` 400 qaytaradi.
  * Yozish atomar: vaqtinchalik fayl + os.replace, oldingi nusxa .bak sifatida saqlanadi.
  * Maxfiy yo'llar (data/, *.py, nuqtali fayllar, testlar) statik tarzda berilmaydi.
"""
from __future__ import annotations

import argparse
import errno
import http.server
import json
import os
import socket
import socketserver
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 5050
PORT_SCAN_LIMIT = 10
MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MB — sozlamalar fayli uchun mo'l-ko'l

# Statik tarzda berilmaydigan yo'llar
BLOCKED_PREFIXES = ("/data", "/tests", "/tools", "/node_modules", "/.git")
BLOCKED_SUFFIXES = (".py", ".pyc", ".bak", ".tmp", ".log", ".md")
NO_STORE_PATHS = ("/sw.js", "/api/data")

_write_lock = threading.Lock()


def data_paths() -> tuple[str, str]:
    """Ma'lumot papkasi va faylini qaytaradi. Testlar ZENITH_DATA_DIR bilan izolyatsiya qiladi."""
    data_dir = os.environ.get("ZENITH_DATA_DIR") or os.path.join(DIRECTORY, "data")
    return data_dir, os.path.join(data_dir, "timer_data.json")


def atomic_write_json(path: str, payload: dict) -> None:
    """Fayl yarim yozilib qolmasligi uchun: tmp -> fsync -> replace, eskisi .bak ga."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    with _write_lock:
        if os.path.exists(path):
            try:
                os.replace(path, path + ".bak")
            except OSError:
                pass
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".timer_data-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


class Handler(http.server.SimpleHTTPRequestHandler):
    """Statik fayllar + /api/data. CORS ataylab berilmaydi."""

    server_version = "ZenithTimer/2.0"
    quiet = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # ----------------------------------------------------------------- yordamchi

    def _send_json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_text(self, status: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _is_blocked(self, path: str) -> bool:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if any(part.startswith(".") for part in clean.split("/") if part):
            return True
        if clean.startswith(BLOCKED_PREFIXES):
            return True
        return clean.endswith(BLOCKED_SUFFIXES)

    def _same_origin(self) -> bool:
        """
        Yozish so'rovi shu sahifadan kelganini tekshiradi.
        Brauzer `Sec-Fetch-Site` yubormasa, `Origin` host bilan solishtiriladi.
        """
        site = self.headers.get("Sec-Fetch-Site")
        if site and site not in ("same-origin", "none"):
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        host = self.headers.get("Host", "")
        return origin.split("://", 1)[-1] == host

    # ------------------------------------------------------------------ metodlar

    def do_OPTIONS(self):  # noqa: N802 (BaseHTTPRequestHandler nomlanishi)
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path.split("?", 1)[0] == "/api/data":
            _, data_file = data_paths()
            if not os.path.exists(data_file):
                self._send_json(200, {})
                return
            try:
                with open(data_file, encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                self.log_error("ma'lumot faylini o'qib bo'lmadi: %s", exc)
                self._send_json(200, {})
                return
            self._send_json(200, payload)
            return

        if self._is_blocked(self.path):
            self._send_text(404, "Not found")
            return
        super().do_GET()

    def do_HEAD(self):  # noqa: N802
        if self._is_blocked(self.path):
            self._send_text(404, "Not found")
            return
        super().do_HEAD()

    def do_POST(self):  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/data":
            self._send_text(404, "Not found")
            return

        if not self._same_origin():
            self.log_message("cross-site POST rad etildi: origin=%s", self.headers.get("Origin"))
            self._send_json(403, {"error": "cross-site request rejected"})
            return

        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if length < 0:
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"error": f"body too large (max {MAX_BODY_BYTES} bytes)"})
            return

        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": f"invalid JSON: {exc}"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "JSON object expected"})
            return

        _, data_file = data_paths()
        try:
            atomic_write_json(data_file, payload)
        except OSError as exc:
            self.log_error("yozishda xatolik: %s", exc)
            self._send_json(500, {"error": "could not persist data"})
            return

        self._send_json(200, {"status": "saved", "savedAt": datetime.now(timezone.utc).isoformat()})

    # ------------------------------------------------------------------ sarlavha

    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path in NO_STORE_PATHS:
            self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    # --------------------------------------------------------------------- log

    def log_message(self, fmt, *args):
        """Jim emas, lekin --quiet bilan o'chiriladi — nosozlikni aniqlash uchun."""
        if self.quiet:
            return
        sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def bind_server(host: str, port: int, scan: int = PORT_SCAN_LIMIT) -> ThreadingServer:
    """Port band bo'lsa keyingilarini sinaydi — server jim yiqilmaydi."""
    last_error: OSError | None = None
    for candidate in range(port, port + max(1, scan)):
        try:
            return ThreadingServer((host, candidate), Handler)
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            last_error = exc
    raise SystemExit(f"❌  {port}–{port + scan - 1} oralig'ida bo'sh port topilmadi: {last_error}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Zenith Study Timer mahalliy serveri")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bog'lanish manzili (standart: 127.0.0.1). 0.0.0.0 — tarmoqqa ochadi.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (standart: {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Brauzerni avtomatik ochmaslik")
    parser.add_argument("--quiet", action="store_true", help="So'rov loglarini o'chirish")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    Handler.quiet = args.quiet

    data_dir, data_file = data_paths()
    os.makedirs(data_dir, exist_ok=True)

    httpd = bind_server(args.host, args.port)
    host, port = httpd.server_address[0], httpd.server_address[1]
    shown_host = "localhost" if host in ("127.0.0.1", "0.0.0.0", "::1") else host
    url = f"http://{shown_host}:{port}"

    print("=" * 62)
    print("⏱  ZENITH STUDY TIMER — SERVER ISHLAMOQDA")
    print(f"🔗  Manzil:        {url}")
    print(f"💾  JSON ombori:   {data_file}")
    if args.host == "0.0.0.0":
        print("⚠️  DIQQAT: server butun tarmoqqa ochiq (--host 0.0.0.0).")
    print("💡  To'xtatish:    Ctrl+C")
    print("=" * 62)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except (webbrowser.Error, OSError):
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Server to'xtatildi.")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
