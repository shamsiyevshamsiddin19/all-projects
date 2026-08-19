# -*- coding: utf-8 -*-
"""Dasturlash (Coding) darsliklarini language_topics jadvaliga yuklash skripti."""
import os
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, LANG = 'global', 'shared', 'coding'

SEEDS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SEEDS_DIR, 'dasturlash_md')

LESSONS_MAP = [
    {
        "folder": "01. Linux & Terminal",
        "name": "1. Linux Terminal Komandalar (Mukammal Qo'llanma)",
        "file": "Terminal_Komandalar.md",
        "image": "assets/img/coding/terminal.jpg",
        "sort_order": 1
    },
    {
        "folder": "02. Python Asoslari & Muhit",
        "name": "1. Python Terminal va Muhit Buyruqlari (Linux)",
        "file": "Python_Terminal_Buyruqlar.md",
        "image": "assets/img/coding/python.jpg",
        "sort_order": 2
    },
    {
        "folder": "02. Python Asoslari & Muhit",
        "name": "2. Python String Metodlari va RegEx Qo'llanmasi",
        "file": "String va RegEx.md",
        "image": "assets/img/coding/regex.jpg",
        "sort_order": 3
    },
    {
        "folder": "03. Versiyalar Nazorati (Git)",
        "name": "1. Git va GitHub To'liq Qo'llanma",
        "file": "Git_Toliq_Qollanma.md",
        "image": "assets/img/coding/git.jpg",
        "sort_order": 4
    },
    {
        "folder": "04. Telegram Bot Dasturlash",
        "name": "1. Aiogram v3 — Noldan Production'gacha Mukammal Qo'llanma",
        "file": "Aiogram_v3_Mukammal_Qollanma.md",
        "image": "assets/img/coding/aiogram.jpg",
        "sort_order": 5
    },
    {
        "folder": "05. Backend & Web (Django & PostgreSQL)",
        "name": "1. Django — Noldan Production'gacha Mukammal Qo'llanma",
        "file": "Django_Mukammal_Qollanma.md",
        "image": "assets/img/coding/django.jpg",
        "sort_order": 6
    },
    {
        "folder": "05. Backend & Web (Django & PostgreSQL)",
        "name": "2. Django + Aiogram + PostgreSQL Integratsiya Qo'llanmasi",
        "file": "Django_Aiogram_PostgreSQL_Qollanma.md",
        "image": "assets/img/coding/fullstack.jpg",
        "sort_order": 7
    }
]

def main():
    print("Eski coding mavzularini tozalash...")
    db.execute(
        "DELETE FROM language_topics WHERE lang = :l",
        {"l": LANG}
    )

    inserted = 0
    for item in LESSONS_MAP:
        file_path = os.path.join(DATA_DIR, item["file"])
        if not os.path.exists(file_path):
            print(f"Fayl topilmadi: {item['file']}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        img_tag = f"![{item['name']}]({item['image']})\n\n"
        if not content.startswith("!["):
            if content.startswith("#"):
                parts = content.split("\n", 1)
                header = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                content = f"{header}\n\n{img_tag}{rest.strip()}"
            else:
                content = f"{img_tag}{content}"

        db.execute(
            """INSERT INTO language_topics 
               (owner_type, owner_key, lang, name, folder, content, sort_order)
               VALUES (:ot, :ok, :l, :n, :f, :c, :so)""",
            {"ot": OT, "ok": OK, "l": LANG, "n": item['name'], 
             "f": item['folder'], "c": content, "so": item['sort_order']}
        )
        inserted += 1
        print(f"Qo'shildi: [{item['folder']}] {item['name']} ({len(content)} belgi)")

    print(f"\nTayyor! Jami {inserted} ta dasturlash mavzusi yuklandi!")

if __name__ == '__main__':
    main()
