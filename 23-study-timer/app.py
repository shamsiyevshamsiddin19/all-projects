#!/usr/bin/env python3
"""
Zenith Study Timer — Python Local Server & JSON Data Store Runner
"""
import http.server
import json
import os
import socketserver
import sys
import webbrowser

PORT = 5050
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIRECTORY, "data")
DATA_FILE = os.path.join(DATA_DIR, "timer_data.json")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"{}")
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/data":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                parsed = json.loads(body.decode("utf-8"))
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"status":"saved"}')
            except (json.JSONDecodeError, OSError) as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass # Silent logging for clean terminal

def main():
    os.chdir(DIRECTORY)
    os.makedirs(DATA_DIR, exist_ok=True)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print("⏱  ZENITH STUDY TIMER — SERVER ISHLAMOQDA")
        print(f"🔗  Manzil: {url}")
        print(f"💾  JSON ma'lumotlar fayli: {DATA_FILE}")
        print("💡  To'xtatish uchun: Ctrl+C")
        print("=" * 60)
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑  Server to'xtatildi.")
            sys.exit(0)

if __name__ == "__main__":
    main()
