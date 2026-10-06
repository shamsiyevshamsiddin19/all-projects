# -*- coding: utf-8 -*-
"""Rus tili darsliklarini language_topics jadvaliga yuklash skripti.

QAYTA ishga tushirishga chidamli: mavjud mavzularni yangilaydi, yo'qlarini qo'shadi.
"""
import os
import glob
import re
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, LANG = 'global', 'shared', 'russian'

SEEDS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SEEDS_DIR, 'rus_tili')
TOPICS_DIR = os.path.join(DATA_DIR, 'mavzular')

def load_lessons():
    items = []
    
    # 0. Qo'llanma
    guide_path = os.path.join(DATA_DIR, '00-KURS-HAQIDA-QOLLANMA.md')
    if os.path.exists(guide_path):
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        items.append({
            'sort_order': 1,
            'folder': "00. Boshlang'ich tayyorgarlik",
            'name': "0. Kurs haqida to'liq qo'llanma",
            'content': content
        })
    
    # Barcha darslar
    files = glob.glob(os.path.join(TOPICS_DIR, '*.md'))
    lesson_list = []
    for f in files:
        base = os.path.basename(f)
        if base == 'barcha_mavzular_ruscha.md':
            continue
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
        
        first_line = content.split('\n')[0].strip()
        m = re.match(r'^#\s*([\d\.]+)[-_]MAVZU:\s*(.+)$', first_line, re.IGNORECASE)
        if m:
            num_str = m.group(1)
            raw_title = m.group(2).strip()
        else:
            m2 = re.match(r'^([\d\.]+)_mavzu_', base)
            num_str = m2.group(1) if m2 else '99'
            raw_title = first_line.lstrip('#').strip()
        
        num_val = float(num_str)
        lesson_list.append((num_val, num_str, raw_title, content, base))
    
    lesson_list.sort(key=lambda x: x[0])
    
    for num_val, num_str, raw_title, content, base in lesson_list:
        if num_val < 1:
            folder = "00. Boshlang'ich tayyorgarlik"
            sub_num = int(round(num_val * 10))
            name = f"{sub_num}. {raw_title}"
        elif num_val <= 8:
            folder = "01. Ot, fe'l, sifat asoslari"
            name = f"{int(num_val)}. {raw_title}"
        elif num_val <= 18:
            folder = "02. Kelishiklar tizimi (1-bosqich)"
            name = f"{int(num_val)}. {raw_title}"
        elif num_val <= 35:
            folder = "03. Kelishiklar tizimi (2-bosqich)"
            name = f"{int(num_val)}. {raw_title}"
        else:
            folder = "04. O'rta daraja (B1–B2)"
            name = f"{int(num_val)}. {raw_title}"
        
        items.append({
            'sort_order': len(items) + 1,
            'folder': folder,
            'name': name,
            'content': content
        })
    
    return items

def main():
    items = load_lessons()
    print(f"Yuklanayotgan mavzular soni: {len(items)}")
    
    inserted = 0
    updated = 0
    
    for item in items:
        existing = db.fetch_one(
            """SELECT id FROM language_topics 
               WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
               AND folder = :f AND name = :n LIMIT 1""",
            {"ot": OT, "ok": OK, "l": LANG, "f": item['folder'], "n": item['name']}
        )
        if existing:
            db.execute(
                """UPDATE language_topics 
                   SET content = :c, sort_order = :so, updated_at = CURRENT_TIMESTAMP
                   WHERE id = :id""",
                {"c": item['content'], "so": item['sort_order'], "id": existing['id']}
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO language_topics 
                   (owner_type, owner_key, lang, name, folder, content, sort_order)
                   VALUES (:ot, :ok, :l, :n, :f, :c, :so)""",
                {"ot": OT, "ok": OK, "l": LANG, "n": item['name'], 
                 "f": item['folder'], "c": item['content'], "so": item['sort_order']}
            )
            inserted += 1
            
    print(f"Tayyor! Yangi qo'shildi: {inserted}, Yangilandi: {updated}, Jami: {inserted + updated}")

if __name__ == '__main__':
    main()
