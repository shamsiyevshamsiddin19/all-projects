# -*- coding: utf-8 -*-
"""Django darsligini saytning Learn > Django bo'limiga yuklaydi.

Manba : ~/Documents/shamsiyev/Dasturlash/Django-Darslik/
Maqsad: lang = lang_1785561197511 (Learn ro'yxatidagi "Django")

Tuzilma — manbadagi kabi IKKI BO'LIM (papka):
  01-bob. Django asosiy kursi        (01-17 dars)
  02-bob. Aiogram + PostgreSQL bot   (18-27 dars)

Mavzu nomlari mundarija jadvalidan olinadi ("№ | Mavzu | Fayl"), shuning
uchun ro'yxatda fayl nomi emas, odam o'qiydigan sarlavha turadi. Nom
boshidagi raqam saytdagi raqamli belgichaga tushadi.

Tartib: `add_topic` ketma-ket chaqiriladi — backend `ORDER BY sort_order, id`
qiladi, sort_order hammada 0, demak qo'shilish tartibi saqlanadi.
"""
import json, os, re, sys, time, urllib.request

BASE = "https://y.wstore.uz/api"
LANG = "lang_1785561197511"
SRC = os.path.expanduser("~/Documents/shamsiyev/Dasturlash/Django-Darslik")
TOC = os.path.join(SRC, "00-django-darslik-mundarija.md")

FOLDERS = [
    ("01-bob-django-asosiy-kurs", "01-bob. Django asosiy kursi"),
    ("02-bob-aiogram-postgresql-bot", "02-bob. Aiogram + PostgreSQL bot"),
]


def api(action, payload=None, query=""):
    url = BASE + "?action=" + action + (("&" + query) if query else "")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode())
    if j.get("success") is False:
        raise RuntimeError(action + ": " + str(j.get("error") or j))
    return j


def titles_from_toc():
    """fayl nomi -> "NN. Sarlavha" """
    out = {}
    for line in open(TOC, encoding="utf-8"):
        m = re.match(r"^\|\s*(\d{2})\s*\|\s*(.+?)\s*\|\s*([\w\-.]+\.md)\s*\|\s*$", line)
        if m:
            out[m.group(3)] = "%s. %s" % (m.group(1), m.group(2))
    return out


def main():
    titles = titles_from_toc()
    print("mundarijadan olingan sarlavhalar:", len(titles))

    have = {(t["folder"], t["name"]) for t in api("get_topics", query="lang=" + LANG)["topics"]}
    added = skipped = 0

    for dirname, folder in FOLDERS:
        d = os.path.join(SRC, dirname)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md"):
                continue
            name = titles.get(fn)
            if not name:                       # mundarijada yo'q — fayl nomidan yasaymiz
                base = fn[:-3]
                m = re.match(r"^(\d+)-(.+)$", base)
                name = ("%s. %s" % (m.group(1), m.group(2).replace("-", " ").capitalize())) if m else base
            if (folder, name) in have:
                print("  o'tkazildi:", folder, "/", name)
                skipped += 1
                continue
            content = open(os.path.join(d, fn), encoding="utf-8").read()
            j = api("add_topic", {"lang": LANG, "name": name, "folder": folder})
            tid = j.get("id") or (j.get("topic") or {}).get("id")
            if not tid:
                raise RuntimeError("id qaytmadi: " + str(j))
            api("upload_topic_content", {"id": tid, "part": "content", "content": content})
            print("  + %-34s %s" % (folder, name))
            added += 1
            time.sleep(0.15)

    print("\nqo'shildi: %d,  o'tkazildi: %d" % (added, skipped))
    topics = api("get_topics", query="lang=" + LANG)["topics"]
    per = {}
    for t in topics:
        per[t["folder"]] = per.get(t["folder"], 0) + 1
    print("Bo'limlar:", per, " Jami:", len(topics))
    print("Matni bor:", sum(1 for t in topics if t.get("has_content")))


main()
