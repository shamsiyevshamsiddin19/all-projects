# -*- coding: utf-8 -*-
"""
Ubuntu 24.04 LTS mukammal Linux darsligini (7 ta bob, 20 ta dars + Maxsus mavzular) language_topics jadvaliga yuklash.
"""
import os
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

LINUX_LANG = 'lang_1785566000100'

from generate_deep_linux_lessons import CHAPTERS

def main():
    base_dir = '/opt/yordamchi/Yordamchisayt/database/seeds/linux_darslik'
    if not os.path.exists(base_dir):
        base_dir = '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Linux-Darslik'

    print(f"Baza: {LINUX_LANG} dagi eski mavzularni tozalash...")
    db.execute("DELETE FROM language_topics WHERE lang = :l", {"l": LINUX_LANG})

    # 1. Add "M. Maxsus mavzular"
    print("M. Maxsus mavzular qo'shilmoqda...")
    special_content = """# Maxsus mavzular

Ushbu bo'lim Ubuntu 24.04 LTS va Linux tizimi bo'yicha maxsus, chuqurlashtirilgan va qo'shimcha amaliy mavzular uchun ajratilgan.

Bu yerga o'zingizning shaxsiy yoki maxsus darslaringizni qo'shishingiz mumkin."""

    db.execute(
        """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
           VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
        {
            "l": LINUX_LANG,
            "f": "M. Maxsus mavzular",
            "n": "M. Maxsus mavzular haqida",
            "c": special_content,
            "so": 0,
            "ot": "global",
            "ok": "shared"
        }
    )

    total_inserted = 1
    sort_counter = 1

    for chap in CHAPTERS:
        folder_name = chap["title"]
        chap_dir = os.path.join(base_dir, chap["dir"])
        print(f"\n📁 Bob: [{folder_name}] ({chap_dir})")

        for lesson in chap["lessons"]:
            fn = lesson["fn"]
            display_title = lesson["name"]
            fp = os.path.join(chap_dir, fn)
            
            if os.path.exists(fp):
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = lesson["content"].strip()

            db.execute(
                """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
                   VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
                {
                    "l": LINUX_LANG,
                    "f": folder_name,
                    "n": display_title,
                    "c": content,
                    "so": sort_counter,
                    "ot": "global",
                    "ok": "shared"
                }
            )
            print(f"  ✅ Yuklandi [{sort_counter}]: {display_title} ({len(content)} bayt)")
            sort_counter += 1
            total_inserted += 1

    print(f"\n🎉 Yakunlandi! Jami {total_inserted} ta mukammal Linux mavzusi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
