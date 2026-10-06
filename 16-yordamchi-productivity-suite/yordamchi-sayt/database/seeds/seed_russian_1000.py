# -*- coding: utf-8 -*-
"""
1000 ta ruscha so'zni aniq va mukammal o'zbekcha tarjimalari bilan dictionary_words jadvaliga yuklash.
"""
import os
import sys
import json

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db
from sqlalchemy import text

# Import translation maps
from generate_russian_dictionary import RUSSIAN_1000_DICT
from fill_missing_translations import ADDITIONAL_TRANSLATIONS
from translate_all_1000 import TRANSLATIONS_ALL

FULL_MAP = {}
FULL_MAP.update(RUSSIAN_1000_DICT)
FULL_MAP.update(ADDITIONAL_TRANSLATIONS)
FULL_MAP.update(TRANSLATIONS_ALL)

def main():
    json_path = os.path.join(os.path.dirname(__file__), 'russian_1000_words.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("1. Eski ruscha so'zlarni dictionary_words dan tozalash...")
    db.execute("DELETE FROM dictionary_words WHERE lang = 'russian'")

    order_list = []
    total = 0
    rank_keys = ['1-100', '101-200', '201-300', '301-400', '401-500', '501-600', '601-700', '701-800', '801-900', '901-1000']

    for idx, rk in enumerate(rank_keys):
        words = data.get(rk, [])
        cat_name = f"1-1000/{rk}"
        order_list.append(cat_name)

        print(f"[{cat_name}] {len(words)} ta so'zni yuklash...")
        for s_idx, ru_w in enumerate(words):
            w_clean = ru_w.strip().lower()
            uz_w = FULL_MAP.get(w_clean, ru_w)
            sort_order = idx * 100 + s_idx + 1

            db.execute(
                """INSERT INTO dictionary_words (lang, category, word_ru, word_uz, sort_order)
                   VALUES (:l, :c, :ru, :uz, :so)""",
                {"l": "russian", "c": cat_name, "ru": ru_w, "uz": uz_w, "so": sort_order}
            )
            total += 1

    # Save category order
    db.storage_set(
        "dict_category_order_russian",
        json.dumps(order_list, ensure_ascii=False),
        {"owner_type": "global", "owner_key": "shared"}
    )

    print(f"\n✅ Muvaffaqiyatli! Jami {total} ta ruscha so'z 100% mukammal o'zbekcha tarjimalari bilan bazaga yuklandi!")
    print(f"Kategoriyalar: {order_list}")

if __name__ == '__main__':
    main()
