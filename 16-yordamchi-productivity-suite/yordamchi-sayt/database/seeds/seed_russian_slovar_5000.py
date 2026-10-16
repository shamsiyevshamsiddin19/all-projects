# -*- coding: utf-8 -*-
"""
'Словарь 5000' (25 ta tematik toifa, 5203 ta so'z) lug'atini dictionary_words jadvaliga yuklash.
"""
import os
import sys
import json

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
try:
    from app import db
except ImportError:
    db = None

def main():
    json_path = os.path.join(os.path.dirname(__file__), 'slovar_5000_words.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    order = data.get('order', [])
    items = data.get('items', [])

    if not db:
        print("Baza ulanishi mavjud emas (faqat serverda ishlaydi).")
        return

    print("1. 'Словарь 5000' ning eski so'zlarini tozalash...")
    db.execute("DELETE FROM dictionary_words WHERE lang = 'russian' AND category LIKE 'Словарь 5000/%'")

    print(f"2. {len(items)} ta so'zni yuklash...")
    for idx, it in enumerate(items):
        db.execute(
            """INSERT INTO dictionary_words (lang, category, word_ru, word_uz, note, example, sort_order)
               VALUES (:l, :c, :ru, :uz, :note, :ex, :so)""",
            {
                "l": "russian",
                "c": it['category'],
                "ru": it['word_ru'],
                "uz": it['word_uz'],
                "note": it.get('note', ''),
                "ex": it.get('example', ''),
                "so": idx + 1
            }
        )
        if (idx + 1) % 500 == 0:
            print(f"  {idx + 1} / {len(items)} yuklandi...")

    # Kategoriya tartibiga qo'shish
    current_order = db.storage_value("dict_category_order_russian", "[]", {"owner_type": "global", "owner_key": "shared"})
    try:
        cur_list = json.loads(current_order)
    except Exception:
        cur_list = []
    
    for cat in order:
        if cat not in cur_list:
            cur_list.append(cat)

    db.storage_set(
        "dict_category_order_russian",
        json.dumps(cur_list, ensure_ascii=False),
        {"owner_type": "global", "owner_key": "shared"}
    )

    print(f"\n✅ Muvaffaqiyatli! Jami {len(items)} ta so'z 'Словарь 5000' bo'yicha bazaga yuklandi!")

if __name__ == '__main__':
    main()
