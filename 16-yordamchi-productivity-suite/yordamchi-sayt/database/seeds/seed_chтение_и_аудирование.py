# -*- coding: utf-8 -*-
"""
Шумская Л.М., Билютенко Е.И. «Чтение и аудирование» (ru_reading) kutubxonasini
PostgreSQL bazasiga to'liq yuklash skripti.

Xususiyatlari:
- 13 ta mavzu bo'yicha jami 130 ta interaktiv matn
- Har bir papka uchun marker (__folder__) yaratadi
- 'user' (shamsiyevshamsiddin19@gmail.com) va 'global' (shared) kontekstlariga yozadi
- Adashib qo'shilgan 'Русские падежи' vaqtinchalik yozuvlarini tozalaydi
"""

import os
import sys
import json

# Backend muhitini ulash
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
try:
    from app import db
except ImportError:
    from backend_py.app import db

JSON_FILE = '/opt/yordamchi/Yordamchisayt/database/seeds/rus_tili/chтение_и_аудирование/chтение_и_аудирование_all.json'
if not os.path.exists(JSON_FILE):
    # Lokal yo'l fallback
    JSON_FILE = os.path.join(os.path.dirname(__file__), 'rus_tili/chтение_и_аудирование/chтение_и_аудирование_all.json')

LANG = 'ru_reading'
OWNERS = [
    ('user', 'shamsiyevshamsiddin19@gmail.com'),
    ('global', 'shared')
]

def main():
    if not os.path.exists(JSON_FILE):
        print(f"XATOLIK: {JSON_FILE} topilmadi!")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    print(f"Jami yuklanayotgan 'Чтение и аудирование' matnlari: {len(records)}")

    # Barcha unikal papkalar
    subfolders = sorted(list(set(r['folder'] for r in records)))
    
    for ot, ok in OWNERS:
        print(f"\n==================================================")
        print(f"Kontekst: {ot} | {ok}")
        print(f"==================================================")

        # 1. Adashib qo'shilgan eski 'Русские падежи' yozuvlarini tozalash
        deleted = db.execute(
            """DELETE FROM language_topics 
               WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
               AND folder LIKE 'Русские падежи%'""",
            {"ot": ot, "ok": ok, "l": LANG}
        )
        print(f"Eski 'Русские падежи' tozalandi: {deleted} ta qator")

        # 2. Bosh papka markeri
        top_marker = db.fetch_one(
            """SELECT id FROM language_topics 
               WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
               AND folder = 'Чтение и аудирование' AND name = '__folder__' LIMIT 1""",
            {"ot": ot, "ok": ok, "l": LANG}
        )
        if not top_marker:
            db.execute(
                """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                   VALUES (:ot, :ok, :l, '__folder__', 'Чтение и аудирование', '', 0)""",
                {"ot": ot, "ok": ok, "l": LANG}
            )
            print("Bosh papka markeri yaratildi: 'Чтение и аудирование'")

        # 3. Ichki mavzu papkalari markerlari
        for fld in subfolders:
            sub_marker = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = '__folder__' LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": fld}
            )
            if not sub_marker:
                db.execute(
                    """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                       VALUES (:ot, :ok, :l, '__folder__', :f, '', 0)""",
                    {"ot": ot, "ok": ok, "l": LANG, "f": fld}
                )

        # 4. Matnlarni upsert qilish
        ins_count = 0
        upd_count = 0
        for r in records:
            existing = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = :n LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": r['folder'], "n": r['name']}
            )
            if existing:
                db.execute(
                    """UPDATE language_topics 
                       SET content = :c, sort_order = :so, updated_at = NOW() 
                       WHERE id = :id""",
                    {"c": r['content'], "so": r['sort_order'], "id": existing['id']}
                )
                upd_count += 1
            else:
                db.execute(
                    """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                       VALUES (:ot, :ok, :l, :n, :f, :c, :so)""",
                    {
                        "ot": ot, "ok": ok, "l": LANG,
                        "n": r['name'], "f": r['folder'],
                        "c": r['content'], "so": r['sort_order']
                    }
                )
                ins_count += 1

        print(f"Natija ({ot}): {ins_count} ta yangi qo'shildi, {upd_count} ta yangilandi.")

    print("\n✅ 'Чтение и аудирование' kitobi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
