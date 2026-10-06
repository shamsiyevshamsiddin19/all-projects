# -*- coding: utf-8 -*-
"""
Python darsligini (7 ta bo'lim, 28 ta dars + Maxsus mavzular) language_topics jadvaliga yuklash.
"""
import os
import sys
import glob
import re

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db
from datetime import datetime

PYTHON_LANG = 'lang_1785560388463'

# Boblar konfiguratsiyasi
CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "folder": "00. Kirish",
        "lessons": [
            ("0.1-python-nima-ornatish.md", "0.1. Python nima, tarixi va o'rnatish"),
            ("0.2-birinchi-dastur-repl-kod-uslubi.md", "0.2. Birinchi dastur, REPL va kod uslubi"),
        ]
    },
    {
        "dir": "01-bob-sintaksis-asoslari",
        "folder": "01. Sintaksis asoslari",
        "lessons": [
            ("1.1-ozgaruvchilar-turlar-operatorlar.md", "1.1. O'zgaruvchilar, ma'lumot turlari va operatorlar"),
            ("1.2-kirish-chiqish-fstring.md", "1.2. Kirish/chiqish va f-string"),
            ("1.3-shart-operatorlari.md", "1.3. Shart operatorlari (if/elif/else, walrus, match-case)"),
            ("1.4-sikllar.md", "1.4. Sikllar (for/while/range/break/continue/else)"),
        ]
    },
    {
        "dir": "02-bob-malumot-tuzilmalari",
        "folder": "02. Ma'lumot tuzilmalari",
        "lessons": [
            ("2.1-satrlar.md", "2.1. Satrlar (strings) bilan ishlash"),
            ("2.2-royxatlar-tuple.md", "2.2. Ro'yxatlar (list) va Tuple"),
            ("2.3-lugatlar-set.md", "2.3. Lug'atlar (dict) va Set"),
            ("2.4-comprehensions.md", "2.4. Comprehensions (list, dict, set)"),
            ("2.5-tuzilma-tanlash-mini-loyiha.md", "2.5. Qaysi tuzilmani qachon tanlash + mini-loyiha"),
        ]
    },
    {
        "dir": "03-bob-funksiyalar-modullar",
        "folder": "03. Funksiyalar va modullar",
        "lessons": [
            ("3.1-funksiyalar-argumentlar-lambda.md", "3.1. Funksiyalar, argumentlar va lambda"),
            ("3.2-scope-closures-rekursiya.md", "3.2. Scope, closures va rekursiya"),
            ("3.3-modullar-paketlar-standart-kutubxona.md", "3.3. Modullar, paketlar va standart kutubxona"),
            ("3.4-virtual-muhit-paket-boshqaruv.md", "3.4. Virtual muhit va paket boshqaruvi (pip, uv)"),
        ]
    },
    {
        "dir": "04-bob-oop",
        "folder": "04. OOP (Obyektga yo'naltirilgan dasturlash)",
        "lessons": [
            ("4.1-klass-obyekt-asoslari.md", "4.1. Klass va obyekt asoslari"),
            ("4.2-meros-super.md", "4.2. Meros (inheritance) va super()"),
            ("4.3-inkapsulyatsiya-property-polimorfizm.md", "4.3. Inkapsulyatsiya, property va polimorfizm"),
            ("4.4-magic-metodlar-dataclasses-enum.md", "4.4. Magic metodlar, dataclasses va Enum"),
            ("4.5-abstract-classes.md", "4.5. Abstract classes (abc moduli)"),
        ]
    },
    {
        "dir": "05-bob-istisno-fayl-generator",
        "folder": "05. Istisnolar, fayllar va generatorlar",
        "lessons": [
            ("5.1-istisnolar.md", "5.1. Istisnolar (exceptions)"),
            ("5.2-fayllar-context-managers.md", "5.2. Fayllar (matn/JSON/CSV) va context managerlar"),
            ("5.3-iteratorlar-generatorlar.md", "5.3. Iteratorlar va generatorlar"),
            ("5.4-dekoratorlar.md", "5.4. Dekoratorlar"),
            ("5.5-type-hints.md", "5.5. Type hints (tur maslahatlari)"),
        ]
    },
    {
        "dir": "06-bob-ilgor-professional",
        "folder": "06. Ilg'or va professional mavzular",
        "lessons": [
            ("6.1-asyncio-concurrency.md", "6.1. Asyncio va concurrency (threading/multiprocessing/GIL)"),
            ("6.2-testlash-pytest-loglash.md", "6.2. Testlash (pytest) va loglash"),
            ("6.3-paketlash-uv-yakuniy-cli-loyiha.md", "6.3. Paketlash, uv va yakuniy CLI loyiha"),
        ]
    }
]

def main():
    base_dir = '/opt/yordamchi/Yordamchisayt/database/seeds/python_darslik'
    if not os.path.exists(base_dir):
        base_dir = '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Python-Darslik'

    print(f"Baza: {PYTHON_LANG} dagi eski mavzularni tozalash...")
    db.execute("DELETE FROM language_topics WHERE lang = :l", {"l": PYTHON_LANG})

    # 1. Add "M. Maxsus mavzular"
    print("M. Maxsus mavzular qo'shilmoqda...")
    special_content = """# Maxsus mavzular

Ushbu bo'lim Python dasturlash tili bo'yicha maxsus, chuqurlashtirilgan va qo'shimcha amaliy mavzular uchun ajratilgan.

Bu yerga o'zingizning shaxsiy yoki maxsus darslaringizni qo'shishingiz mumkin."""
    
    db.execute(
        """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
           VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
        {
            "l": PYTHON_LANG,
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
        folder_name = chap["folder"]
        chap_dir = os.path.join(base_dir, chap["dir"])
        print(f"\n📁 Bob: [{folder_name}] ({chap_dir})")

        for fn, display_title in chap["lessons"]:
            fp = os.path.join(chap_dir, fn)
            if not os.path.exists(fp):
                print(f"  ❌ Fayl topilmadi: {fp}")
                continue
            
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()

            db.execute(
                """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
                   VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
                {
                    "l": PYTHON_LANG,
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

    print(f"\n🎉 Yakunlandi! Jami {total_inserted} ta Python mavzusi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
