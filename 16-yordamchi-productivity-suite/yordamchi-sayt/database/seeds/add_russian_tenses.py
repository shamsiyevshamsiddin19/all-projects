# -*- coding: utf-8 -*-
"""Rus tili 05-bob Zamonlar darslarini language_topics jadvaliga yuklash."""
import os
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, LANG = 'global', 'shared', 'russian'
FOLDER = '05. Времена глагола (Zamonlar)'

DATA_DIR = '/opt/yordamchi/Yordamchisayt/database/seeds/rus_tili/mavzular/05-bob-zamonlar'

LESSONS = [
    {
        "name": "1. Настоящее время (Hozirgi zamon)",
        "file": "01-Nastoyashee-vremya.md",
        "sort_order": 1
    },
    {
        "name": "2. Прошедшее время (O'tgan zamon)",
        "file": "02-Proshedshee-vremya.md",
        "sort_order": 2
    },
    {
        "name": "3. Будущее время (Kelasi zamon)",
        "file": "03-Budushee-vremya.md",
        "sort_order": 3
    },
    {
        "name": "4. Виды глагола: НСВ и СВ (Fe'l turlari)",
        "file": "04-Vidi-glagola-NSV-SV.md",
        "sort_order": 4
    },
    {
        "name": "5. Глаголы движения во временах (Harakat fe'llari)",
        "file": "05-Glagoli-dvijeniya-vremena.md",
        "sort_order": 5
    },
    {
        "name": "6. Сводная таблица и тесты (Barcha zamonlar jadvali va testlar)",
        "file": "06-Svodnaya-tablitsa-vremen.md",
        "sort_order": 6
    }
]

def main():
    print(f"[{FOLDER}] darslarini yuklash...")
    
    # Clean previous records in this folder if any
    db.execute(
        """DELETE FROM language_topics 
           WHERE owner_type = :ot AND owner_key = :ok AND lang = :l AND folder = :f""",
        {"ot": OT, "ok": OK, "l": LANG, "f": FOLDER}
    )

    inserted = 0
    for item in LESSONS:
        file_path = os.path.join(DATA_DIR, item["file"])
        if not os.path.exists(file_path):
            print(f"Fayl topilmadi: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        db.execute(
            """INSERT INTO language_topics 
               (owner_type, owner_key, lang, name, folder, content, sort_order)
               VALUES (:ot, :ok, :l, :n, :f, :c, :so)""",
            {"ot": OT, "ok": OK, "l": LANG, "n": item['name'], 
             "f": FOLDER, "c": content, "so": item['sort_order']}
        )
        inserted += 1
        print(f"Qo'shildi: [{FOLDER}] {item['name']} ({len(content)} belgi)")

    print(f"\nTayyor! Jami {inserted} ta yangi zamon darsligi yuklandi!")

if __name__ == '__main__':
    main()
