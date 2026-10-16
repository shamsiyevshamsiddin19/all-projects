# -*- coding: utf-8 -*-
"""
JSON fayldan 130 ta .md faylni mahalliy papkalarga yoyish skripti.
"""
import os
import re
import json

JSON_FILE = '/home/shamsiddin/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/database/seeds/rus_tili/chтение_и_аудирование/chтение_и_аудирование_all.json'
SEEDS_DIR = '/home/shamsiddin/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/database/seeds/rus_tili/chтение_и_аудирование'
DOCS_DIR = '/home/shamsiddin/Documents/shamsiyev/Rus tili/kitob/chтение_и_аудирование'

def main():
    if not os.path.exists(JSON_FILE):
        print(f"File not found: {JSON_FILE}")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    print(f"Unpacking {len(records)} records...")
    
    for r in records:
        folder = r['folder']
        # e.g. Чтение и аудирование/01. О себе и не только
        subfolder = folder.split('/', 1)[1] if '/' in folder else folder
        name = r['name'] # e.g. 01. [А1] Студент из Америки
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name) + '.md'
        
        target_seed_dir = os.path.join(SEEDS_DIR, subfolder)
        target_doc_dir = os.path.join(DOCS_DIR, subfolder)
        os.makedirs(target_seed_dir, exist_ok=True)
        os.makedirs(target_doc_dir, exist_ok=True)
        
        with open(os.path.join(target_seed_dir, safe_name), 'w', encoding='utf-8') as sf:
            sf.write(r['content'])
        with open(os.path.join(target_doc_dir, safe_name), 'w', encoding='utf-8') as df:
            df.write(r['content'])
            
    print("Unpack complete!")

if __name__ == '__main__':
    main()
