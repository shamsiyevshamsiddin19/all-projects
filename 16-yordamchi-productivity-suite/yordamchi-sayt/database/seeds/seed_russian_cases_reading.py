# -*- coding: utf-8 -*-
"""
Русские падежи (Мелех, Баранова) — Reading (ru_reading) kutubxonasiga yuklash skripti.

QAYTA ishga tushirishga to'liq chidamli (idempotent):
- Mavjud mavzularni yangilaydi (UPDATE)
- Yo'qlarini qo'shadi (INSERT)
- Papka markerlarini (__folder__) to'g'ri o'rnatadi
- Ham 'user' (shamsiyevshamsiddin19@gmail.com), ham 'global' kontekstlariga yozadi
"""

import sys
import os

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
try:
    from app import db
except ImportError:
    # Lokal test rejimida
    from backend_py.app import db

from rus_tili.padejlar_reading.data import TEXTS

LANG = 'ru_reading'
OWNERS = [
    ('user', 'shamsiyevshamsiddin19@gmail.com'),
    ('global', 'shared')
]

SUBFOLDERS = sorted(list(set(t['folder'] for t in TEXTS)))

def main():
    print(f"Jami yuklanayotgan matnlar soni: {len(TEXTS)}")
    
    total_inserted = 0
    total_updated = 0
    
    for ot, ok in OWNERS:
        print(f"\n--- Kontekst: {ot} | {ok} ---")
        
        # 1. Papka markerlarini o'rnatish
        for fld in SUBFOLDERS:
            existing_marker = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = '__folder__' LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": fld}
            )
            if not existing_marker:
                db.execute(
                    """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                       VALUES (:ot, :ok, :l, '__folder__', :f, '', 1)""",
                    {"ot": ot, "ok": ok, "l": LANG, "f": fld}
                )
                print(f"  + Marker qo'shildi: {fld}")

        # 2. Matnlarni yuklash
        sort_order = 100
        for item in TEXTS:
            fld = item['folder']
            name = item['name']
            content = item['content']
            sort_order += 10
            
            existing = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = :n LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": fld, "n": name}
            )
            
            if existing:
                db.execute(
                    """UPDATE language_topics 
                       SET content = :c, sort_order = :so, updated_at = CURRENT_TIMESTAMP
                       WHERE id = :id""",
                    {"c": content, "so": sort_order, "id": existing['id']}
                )
                total_updated += 1
            else:
                db.execute(
                    """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                       VALUES (:ot, :ok, :l, :n, :f, :c, :so)""",
                    {"ot": ot, "ok": ok, "l": LANG, "n": name, "f": fld, "c": content, "so": sort_order}
                )
                total_inserted += 1
                
    print(f"\nTayyor! Yangi qo'shildi: {total_inserted}, yangilandi: {total_updated}")

if __name__ == '__main__':
    main()
