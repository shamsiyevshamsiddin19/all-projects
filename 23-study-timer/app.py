#!/usr/bin/env python3
"""
Zenith Study Timer — Python Local Server & App Runner
"""
import http.server
import os
import socketserver
import sys
import webbrowser

PORT = 5050
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass # Silent logging for clean terminal

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print("⏱  ZENITH STUDY TIMER — SERVER ISHLAMOQDA")
        print(f"🔗  Manzil: {url}")
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
