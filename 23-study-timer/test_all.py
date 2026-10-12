#!/usr/bin/env python3
"""
Zenith Study Timer — to'liq test to'plami.

Bo'limlar:
  1. Backend: xavfsizlik, API, atomar yozish (izolyatsiyalangan vaqtinchalik papkada).
  2. Statik tuzilma: HTML ↔ JS ↔ CSS ↔ i18n mosligi, a11y, PWA fayllari.
  3. Node mantiq testlari (node --test) — haqiqiy assertion'lar.
  4. jsdom / Playwright holati haqida ma'lumot.

Muhim: bu skript loyihaning haqiqiy data/ papkasiga tegmaydi.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

from bs4 import BeautifulSoup

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TEST_PORT = 5058

# Testlar haqiqiy ma'lumotni buzmasligi uchun — vaqtinchalik papka
TEST_DATA_DIR = tempfile.mkdtemp(prefix="zenith-test-")
os.environ["ZENITH_DATA_DIR"] = TEST_DATA_DIR

_spec = importlib.util.spec_from_file_location("zenith_app", os.path.join(DIRECTORY, "app.py"))
app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app)


class Results:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, details: str = "") -> bool:
        if ok:
            self.passed += 1
            print(f"  ✅ {name} {details}".rstrip())
        else:
            self.failed += 1
            self.failures.append(f"{name} {details}".strip())
            print(f"  ❌ {name} {details}".rstrip())
        return ok


R = Results()


# =============================================================================
# 1. BACKEND
# =============================================================================

def backend_tests() -> None:
    print("\n[1/4] BACKEND: xavfsizlik, API va atomar yozish")
    app.Handler.quiet = True
    server = app.bind_server("127.0.0.1", TEST_PORT)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method: str, path: str, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(method, path, body, headers or {})
        res = conn.getresponse()
        payload = res.read()
        info = (res.status, {k.lower(): v for k, v in res.getheaders()}, payload)
        conn.close()
        return info

    try:
        R.check("Standart bog'lanish manzili 127.0.0.1",
                app.parse_args([]).host == "127.0.0.1",
                "(tarmoqqa ochilmaydi)")

        status, _, body = request("GET", "/")
        R.check("GET / asosiy sahifani beradi", status == 200 and b"ZENITH CHRONO" in body)

        status, headers, _ = request("GET", "/js/app.js")
        R.check("ES modul fayli beriladi", status == 200 and "javascript" in
                headers.get("content-type", ""), f"({headers.get('content-type')})")

        status, _, body = request("GET", "/api/data")
        R.check("Bo'sh ombor {} qaytaradi", status == 200 and json.loads(body) == {})

        payload = json.dumps({"settings": {"volume": 42}, "savedAt": "2026-01-01T00:00:00.000Z"})
        status, headers, _ = request("POST", "/api/data", payload,
                                     {"Content-Type": "application/json"})
        R.check("POST /api/data saqlaydi", status == 200)
        R.check("CORS wildcard yo'q", "access-control-allow-origin" not in headers)

        status, _, body = request("GET", "/api/data")
        R.check("GET saqlangan ma'lumotni qaytaradi (ombor o'qiladi ham)",
                status == 200 and json.loads(body)["settings"]["volume"] == 42)

        status, _, _ = request("POST", "/api/data", "{}", {
            "Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"})
        R.check("Cross-site POST rad etiladi", status == 403)

        status, _, _ = request("POST", "/api/data", "{}", {"Content-Length": "not-a-number"})
        R.check("Buzilgan Content-Length 400 beradi", status == 400)

        big = json.dumps({"x": "y" * (app.MAX_BODY_BYTES + 100)})
        status, _, _ = request("POST", "/api/data", big, {"Content-Type": "application/json"})
        R.check("Haddan katta body 413 bilan rad etiladi", status == 413)

        status, _, _ = request("POST", "/api/data", "[1,2,3]", {"Content-Type": "application/json"})
        R.check("Massiv emas, obyekt talab qilinadi", status == 400)

        status, _, _ = request("POST", "/api/data", "{buzuq", {"Content-Type": "application/json"})
        R.check("Buzilgan JSON 400 beradi", status == 400)

        status, _, _ = request("POST", "/api/boshqa", "{}")
        R.check("Noma'lum API yo'li 404", status == 404)

        for blocked in ("/app.py", "/data/timer_data.json", "/test_all.py", "/.gitignore", "/README.md"):
            status, _, _ = request("GET", blocked)
            R.check(f"Maxfiy yo'l berilmaydi: {blocked}", status == 404, f"(status={status})")

        # Atomar yozish: ikkinchi yozuvdan keyin .bak paydo bo'ladi
        request("POST", "/api/data", json.dumps({"settings": {"volume": 7}}),
                {"Content-Type": "application/json"})
        data_file = os.path.join(TEST_DATA_DIR, "timer_data.json")
        R.check("Zaxira nusxa (.bak) yaratiladi", os.path.exists(data_file + ".bak"))
        R.check("Vaqtinchalik .tmp fayllar qolmaydi",
                not [f for f in os.listdir(TEST_DATA_DIR) if f.endswith(".tmp")])

        status, headers, _ = request("GET", "/sw.js")
        R.check("sw.js keshlanmaydi", status == 200 and
                headers.get("cache-control") == "no-store", f"({headers.get('cache-control')})")

        status, _, body = request("GET", "/manifest.webmanifest")
        R.check("PWA manifesti beriladi", status == 200 and b'"icons"' in body)

        R.check("Testlar haqiqiy data/ papkasini buzmaydi",
                TEST_DATA_DIR != os.path.join(DIRECTORY, "data"))
    finally:
        server.shutdown()
        server.server_close()


# =============================================================================
# 2. STATIK TUZILMA
# =============================================================================

def read(path: str) -> str:
    with open(os.path.join(DIRECTORY, path), encoding="utf-8") as handle:
        return handle.read()


def js_sources() -> dict[str, str]:
    out = {}
    for root, _dirs, files in os.walk(os.path.join(DIRECTORY, "js")):
        for name in files:
            if name.endswith(".js"):
                full = os.path.join(root, name)
                out[os.path.relpath(full, DIRECTORY)] = open(full, encoding="utf-8").read()
    return out


def node_json(expression: str):
    """Node orqali modul eksportidan qiymat oladi."""
    code = f"process.stdout.write(JSON.stringify({expression}))"
    proc = subprocess.run(["node", "--input-type=module", "-e", code],
                          cwd=DIRECTORY, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return json.loads(proc.stdout)


# JS tomonidan dinamik qo'shiladigan yoki brauzer holatiga tegishli klasslar
DYNAMIC_CSS_ALLOWLIST = {
    "active", "open", "paused", "hidden-col", "user-idle", "drawer-open",
    "is-rotated-90", "mobile-pseudo-fullscreen", "digit-pulse", "preset-accent"
}


def structure_tests() -> None:
    print("\n[2/4] STATIK TUZILMA: HTML ↔ JS ↔ CSS ↔ i18n mosligi")
    html = read("index.html")
    css = read("css/style.css")
    soup = BeautifulSoup(html, "html.parser")
    html_ids = {el["id"] for el in soup.select("[id]")}
    sources = js_sources()
    all_js = "\n".join(sources.values())

    # --- 2.1 JS kutgan har bir element HTML'da bormi? (eski "null element" xatosi) ---
    required = set(node_json("(await import('./js/ui.js')).REQUIRED_IDS"))
    missing_required = sorted(required - html_ids)
    R.check("ui.js dagi REQUIRED_IDS to'liq HTML'da bor",
            not missing_required, f"yetishmayapti: {missing_required}" if missing_required else "")

    referenced = set(re.findall(r"getElementById\(['\"]([\w-]+)['\"]\)", all_js))
    referenced |= set(re.findall(r"querySelector(?:All)?\(['\"]#([\w-]+)", all_js))
    ghost_ids = sorted(referenced - html_ids)
    R.check("JS faqat mavjud elementlarga murojaat qiladi",
            not ghost_ids, f"mavjud emas: {ghost_ids}" if ghost_ids else "")

    # --- 2.2 O'lik CSS detektori ---
    css_clean = re.sub(r"/\*.*?\*/", "", css, flags=re.S)       # izohlar
    css_clean = re.sub(r"url\([^)]*\)", "", css_clean)            # url(...) ichidagi nuqtalar
    css_clean = re.sub(r'"[^"]*"|\'[^\']*\'', "", css_clean)       # qolgan matn literallari
    css_classes = set(re.findall(r"\.([a-zA-Z][\w-]*)", css_clean))
    used_text = html + all_js
    dead = sorted(
        cls for cls in css_classes
        if cls not in DYNAMIC_CSS_ALLOWLIST
        and re.search(rf"\b{re.escape(cls)}\b", used_text) is None
    )
    R.check("CSS'da o'lik klass qolmagan", not dead, f"ishlatilmaydi: {dead}" if dead else "")

    # --- 2.3 i18n kalitlari ---
    i18n_keys = set(node_json("(await import('./js/i18n.js')).keysOf('uz')"))
    html_keys = set()
    for attr in ("data-i18n", "data-i18n-title", "data-i18n-aria", "data-i18n-placeholder"):
        html_keys |= {el[attr] for el in soup.select(f"[{attr}]")}
    js_keys = set(re.findall(r"\bt\('([\w.]+)'", all_js))
    unknown = sorted((html_keys | js_keys) - i18n_keys)
    R.check("Barcha i18n kalitlari lug'atda bor",
            not unknown, f"noma'lum: {unknown}" if unknown else "")
    R.check("HTML'dagi matnlar tarjima qilinadi", len(html_keys) > 80, f"({len(html_keys)} ta kalit)")

    # --- 2.4 Rejimlar ---
    tabs = soup.select(".mode-tab")
    modes = {tab.get("data-mode") for tab in tabs}
    R.check("Beshta ish rejimi mavjud (README bilan mos)",
            modes == {"target", "duration", "pomodoro", "stopwatch", "clock"}, f"({sorted(modes)})")
    for tab in tabs:
        panel_id = tab.get("aria-controls")
        if not R.check(f"'{tab.get('data-mode')}' rejimi uchun panel bor",
                       panel_id in html_ids, f"(aria-controls={panel_id})"):
            break

    # --- 2.5 A11y ---
    R.check("Tab tugmalarida role='tab' bor", all(t.get("role") == "tab" for t in tabs))
    R.check("Tab tugmalarida aria-selected bor", all(t.has_attr("aria-selected") for t in tabs))
    R.check("Panellarda role='tabpanel' bor",
            all(soup.find(id=t.get("aria-controls")).get("role") == "tabpanel" for t in tabs))
    R.check("Panel role='dialog' bilan belgilangan",
            soup.find(id="settingsDrawer").get("role") == "dialog")
    R.check("Raqamlar uchun aria-live hudud bor",
            soup.find(id="srAnnounce").get("aria-live") == "polite")
    R.check("Taymer klaviatura bilan fokuslanadi",
            soup.find(id="digitsContainer").get("tabindex") == "0")

    orphan_labels = [
        str(lbl)[:60] for lbl in soup.find_all("label")
        if not lbl.get("for") and not lbl.find(["input", "select", "textarea"])
    ]
    R.check("Har bir <label> boshqaruvga bog'langan",
            not orphan_labels, f"bog'lanmagan: {len(orphan_labels)}" if orphan_labels else "")

    inline_hidden = re.findall(r'style="[^"]*display:\s*none', html)
    R.check("Inline 'display:none' ishlatilmagan (hidden atributi)", not inline_hidden)

    # --- 2.6 CSS sifat tekshiruvlari ---
    R.check("prefers-reduced-motion qo'llanilgan", "prefers-reduced-motion" in css)
    R.check("Mobil balandlik uchun dvh fallback bor", css.count("100dvh") >= 4)
    R.check("Fokus ko'rinadigan (:focus-visible)", ":focus-visible" in css)

    # --- 2.7 PWA ---
    manifest = json.loads(read("manifest.webmanifest"))
    R.check("Manifest nomi va start_url to'g'ri",
            manifest["name"] and manifest["start_url"].endswith("index.html"))
    icons_ok = all(os.path.exists(os.path.join(DIRECTORY, icon["src"])) for icon in manifest["icons"])
    R.check("Manifestdagi barcha ikonalar mavjud", icons_ok)
    R.check("Maskable ikona bor", any(i.get("purpose") == "maskable" for i in manifest["icons"]))
    R.check("Service worker app shell'ni keshlaydi", "SHELL_ASSETS" in read("sw.js"))

    sw = read("sw.js")
    shell = set(re.findall(r"'\./([^']+)'", sw.split("SHELL_ASSETS")[1].split("]")[0]))
    missing_shell = sorted(p for p in shell if p and not os.path.exists(os.path.join(DIRECTORY, p)))
    R.check("Keshlanadigan fayllar mavjud",
            not missing_shell, f"yo'q: {missing_shell}" if missing_shell else "")

    # --- 2.8 Repo gigiyenasi ---
    gitignore = read(".gitignore")
    R.check("data/ papkasi git'ga tushmaydi", "data/" in gitignore)
    R.check("node_modules e'tiborsiz qoldiriladi", "node_modules" in gitignore)
    R.check("requirements.txt mavjud", os.path.exists(os.path.join(DIRECTORY, "requirements.txt")))
    R.check("package.json mavjud", os.path.exists(os.path.join(DIRECTORY, "package.json")))
    R.check("LICENSE mavjud", os.path.exists(os.path.join(DIRECTORY, "LICENSE")))

    # --- 2.9 README haqiqatga mos ---
    readme = read("README.md")
    R.check("README'da maxsus Target preset afsonasi yo'q", "demo_photo" not in readme)
    R.check("README'da test buyrug'i bor", "test_all.py" in readme)
    R.check("README klaviatura jadvalida S bor", re.search(r"`S`", readme) is not None)


# =============================================================================
# 3. NODE MANTIQ TESTLARI
# =============================================================================

def node_tests() -> None:
    print("\n[3/4] NODE MANTIQ TESTLARI (node --test)")
    if shutil.which("node") is None:
        R.check("Node.js mavjud", False, "(o'rnatilmagan — mantiq testlari o'tkazilmadi)")
        return
    proc = subprocess.run(["node", "--test", "tests/*.test.mjs"],
                          cwd=DIRECTORY, capture_output=True, text=True, timeout=180)
    out = proc.stdout
    passed = re.search(r"^# pass (\d+)$", out, re.M)
    failed = re.search(r"^# fail (\d+)$", out, re.M)
    skipped = re.search(r"^# skip(?:ped)? (\d+)$", out, re.M)
    n_pass = int(passed.group(1)) if passed else 0
    n_fail = int(failed.group(1)) if failed else 1
    n_skip = int(skipped.group(1)) if skipped else 0

    if n_fail:
        for line in out.splitlines():
            if line.startswith("not ok") or "error:" in line:
                print(f"     {line.strip()}")
    R.check("Node mantiq testlari o'tdi", n_fail == 0,
            f"({n_pass} ta o'tdi, {n_fail} ta yiqildi, {n_skip} ta o'tkazib yuborildi)")
    R.check("Mantiq testlari yetarlicha keng", n_pass >= 35, f"({n_pass} ta tekshiruv)")


# =============================================================================
# 4. IXTIYORIY TEST QATLAMLARI
# =============================================================================

def optional_layers() -> None:
    print("\n[4/4] IXTIYORIY QATLAMLAR")
    has_jsdom = subprocess.run(["node", "-e", "require.resolve('jsdom')"],
                               cwd=DIRECTORY, capture_output=True).returncode == 0
    print(f"  {'✅' if has_jsdom else 'ℹ️ '} jsdom DOM testlari: "
          f"{'yoqilgan' if has_jsdom else 'o`tkazib yuborildi — `npm install` bilan yoqiladi'}")
    has_pw = os.path.isdir(os.path.join(DIRECTORY, "node_modules", "@playwright"))
    print(f"  {'✅' if has_pw else 'ℹ️ '} Playwright E2E: "
          f"{'tayyor (npm run test:e2e)' if has_pw else 'o`rnatilmagan — `npm run setup:e2e`'}")
    R.check("E2E stsenariy fayli mavjud",
            os.path.exists(os.path.join(DIRECTORY, "tests", "e2e.spec.mjs")))


def main() -> int:
    print("=" * 66)
    print("🚀 ZENITH STUDY TIMER — TEST TO'PLAMI")
    print("=" * 66)
    try:
        backend_tests()
        structure_tests()
        node_tests()
        optional_layers()
    finally:
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    total = R.passed + R.failed
    print("\n" + "=" * 66)
    if R.failed == 0:
        print(f"🎉 BARCHA TESTLAR O'TDI: {R.passed}/{total}")
    else:
        print(f"❌ YIQILGAN TESTLAR: {R.failed}/{total}")
        for item in R.failures:
            print(f"   • {item}")
    print("=" * 66)
    return 1 if R.failed else 0


if __name__ == "__main__":
    sys.exit(main())
