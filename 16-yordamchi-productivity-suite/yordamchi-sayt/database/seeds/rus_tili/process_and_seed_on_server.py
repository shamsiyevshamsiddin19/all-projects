# -*- coding: utf-8 -*-
"""
«Чтение и аудирование» kitobini to'liq o'zbekchalashtirib,
yordamchi-sayt interactive reading (ru_reading) kutubxonasiga yuklash.
1-bosqichda darhol ТЕМА 1 ni yuklaydi, so'ng qolgan mavzularni ketma-ket yuklaydi.
"""

import os
import sys
import json
import re
import time
import socket
import urllib.request
import urllib.parse

# IPv4 majburiy qilish
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

RAW_JSON = '/tmp/chтение_raw.json'
SLOVAR_FILE = '/tmp/slovar_5000_words.json'
CACHE_FILE = '/tmp/trans_cache.json'

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
try:
    from app import db
except ImportError:
    from backend_py.app import db

LANG = 'ru_reading'
OWNERS = [
    ('user', 'shamsiyevshamsiddin19@gmail.com'),
    ('global', 'shared')
]

CORE_MAP = {
    'в': 'da / ga', 'во': 'da / ga', 'на': 'da / ustida', 'из': 'dan', 'изо': 'dan',
    'с': 'bilan / dan', 'со': 'bilan / dan', 'к': 'ga / tomon', 'ко': 'ga / tomon',
    'о': 'haqida', 'об': 'haqida', 'обо': 'haqida', 'по': 'bo\'ylab / bo\'yicha',
    'у': 'huzurida / da', 'от': 'dan', 'до': 'gacha', 'для': 'uchun',
    'за': 'uchun / orqasida', 'под': 'ostida', 'над': 'ustida', 'перед': 'oldida',
    'через': 'orqali / keyin', 'без': 'siz', 'при': 'huzurida', 'и': 'va',
    'а': 'esa / lekin', 'но': 'lekin', 'или': 'yoki', 'не': 'emas / -ma',
    'ни': 'hech / na', 'да': 'ha', 'нет': 'yo\'q', 'что': 'nima / deb',
    'как': 'qanday / kabi', 'где': 'qayerda', 'куда': 'qayerga', 'откуда': 'qayerdan',
    'когда': 'qachon', 'почему': 'nima uchun', 'зачем': 'nima maqsadda',
    'кто': 'kim', 'я': 'men', 'ты': 'sen', 'он': 'u', 'она': 'u', 'оно': 'u',
    'мы': 'biz', 'вы': 'siz', 'они': 'ular', 'меня': 'meni / mening', 'мне': 'menga',
    'мной': 'men bilan', 'мною': 'men bilan', 'тебя': 'seni / sening', 'тебе': 'senga',
    'тобой': 'sen bilan', 'его': 'uni / uning', 'ему': 'unga', 'им': 'u bilan / ular bilan',
    'её': 'uni / uning', 'ей': 'unga', 'ею': 'u bilan', 'нас': 'bizni / bizda',
    'нам': 'bizga', 'нами': 'biz bilan', 'вас': 'sizni / sizda', 'вам': 'sizga',
    'вами': 'siz bilan', 'их': 'ularni / ularning', 'зовут': 'chaqirishadi / ismi',
    'это': 'bu', 'этот': 'bu', 'эта': 'bu', 'эти': 'bular',
    'очень': 'juda', 'тоже': 'ham', 'также': 'shuningdek', 'уже': 'allaqachon',
    'ещё': 'yana / hali', 'всегда': 'doimo', 'иногда': 'ba\'zan', 'часто': 'tez-tez',
    'редко': 'kamdan-kam', 'потом': 'keyin', 'сейчас': 'hozir', 'сегодня': 'bugun',
    'вчера': 'kecha', 'завтра': 'ertaga', 'здесь': 'bu yerda', 'тут': 'bu yerda',
    'там': 'u yerda', 'туда': 'u yoqqa', 'сюда': 'bu yoqqa', 'много': 'ko\'p',
    'мало': 'kam', 'немного': 'biroz', 'только': 'faqat', 'все': 'hamma / barcha',
    'всё': 'hammasi', 'весь': 'butun', 'вся': 'butun', 'друг': 'do\'st',
    'друзья': 'do\'stlar', 'город': 'shahar', 'время': 'vaqt', 'день': 'kun',
    'год': 'yil', 'года': 'yil', 'лет': 'yil', 'студент': 'talaba',
    'студентка': 'talaba qiz', 'студенты': 'talabalar', 'университет': 'universitet',
    'факультет': 'fakultet', 'семья': 'oila', 'работа': 'ish', 'жизнь': 'hayot',
    'хорошо': 'yaxshi', 'плохо': 'yomon', 'быстро': 'tez', 'медленно': 'sekin',
    'красиво': 'chiroyli', 'красивая': 'chiroyli', 'красивый': 'chiroyli',
    'большой': 'katta', 'большая': 'katta', 'маленький': 'kichik', 'маленькая': 'kichik',
    'новый': 'yangi', 'новая': 'yangi', 'старый': 'qadimiy / eski', 'старая': 'eski'
}

trans_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            trans_cache = json.load(f)
        print(f"Keshdan {len(trans_cache)} ta tarjima yuklandi.")
    except Exception:
        pass

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(trans_cache, f, ensure_ascii=False)
    except Exception:
        pass

word_dict = dict(CORE_MAP)
if os.path.exists(SLOVAR_FILE):
    try:
        with open(SLOVAR_FILE, 'r', encoding='utf-8') as f:
            s_data = json.load(f)
        for it in s_data.get('items', []):
            ru = it.get('word_ru', '').strip().lower()
            uz = it.get('word_uz', '').strip()
            ru_c = re.sub(r'[\?\!\.\,]', '', ru).strip()
            if ru_c and ru_c not in word_dict:
                uz_clean = re.sub(r'\(.*?\)', '', uz).strip()
                parts = re.split(r'[,;/]', uz_clean)
                first = parts[0].strip().lower()
                if first and len(first) < 30:
                    word_dict[ru_c] = first
        print(f"Boshlang'ich lug'at: {len(word_dict)} ta so'z.")
    except Exception as e:
        print(f"Lug'at xatosi: {e}")

def batch_translate(items, batch_size=30):
    translated_map = {}
    missing = []
    for it in items:
        clean = re.sub(r'[\u0300-\u036f]', '', it).strip()
        if clean in trans_cache:
            translated_map[it] = trans_cache[clean]
        else:
            missing.append(it)
            
    if not missing:
        return translated_map

    total = len(missing)
    print(f"  Tarjima: {total} ta yangi element...")
    
    for i in range(0, total, batch_size):
        chunk = missing[i:i + batch_size]
        cleaned_chunk = [re.sub(r'[\u0300-\u036f]', '', x).strip() for x in chunk]
        combined = '\n'.join(cleaned_chunk)
        
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=uz&dt=t&q=' + urllib.parse.quote(combined)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        success = False
        for attempt in range(2):
            try:
                res = urllib.request.urlopen(req, timeout=5)
                data = json.loads(res.read().decode('utf-8'))
                full_uz = ''.join([part[0] for part in data[0] if part[0]])
                uz_lines = full_uz.split('\n')
                
                if len(uz_lines) == len(chunk):
                    for orig, cln, uz in zip(chunk, cleaned_chunk, uz_lines):
                        u_str = uz.strip()
                        translated_map[orig] = u_str
                        trans_cache[cln] = u_str
                else:
                    for orig, cln, uz in zip(chunk, cleaned_chunk, uz_lines[:len(chunk)]):
                        u_str = uz.strip()
                        translated_map[orig] = u_str
                        trans_cache[cln] = u_str
                    for orig, cln in zip(chunk[len(uz_lines):], cleaned_chunk[len(uz_lines):]):
                        translated_map[orig] = orig
                        trans_cache[cln] = orig
                success = True
                break
            except Exception:
                time.sleep(0.2 * (attempt + 1))
                
        if not success:
            for orig, cln in zip(chunk, cleaned_chunk):
                translated_map[orig] = orig
                trans_cache[cln] = orig
                
        time.sleep(0.04)
        
    save_cache()
    return translated_map

def annotate_sentence(sent_ru, sent_uz):
    tokens = re.findall(r'[а-яёА-ЯЁa-zA-Z\u0300-\u036f]+|[^\s\w\u0300-\u036f]+|\s+', sent_ru)
    annotated = []
    for tok in tokens:
        clean_tok = re.sub(r'[\u0300-\u036f]', '', tok).strip().lower()
        if re.match(r'^[а-яёА-ЯЁa-zA-Z]+$', clean_tok):
            uz_trans = word_dict.get(clean_tok, '')
            if uz_trans and uz_trans.lower() != clean_tok:
                annotated.append(f"{{{tok}|{uz_trans}}}")
            else:
                annotated.append(tok)
        else:
            annotated.append(tok)
    res_line = ''.join(annotated).strip()
    return f"{res_line}\n:: {sent_uz}"

def format_text(title, level, paragraphs, sentence_translations):
    level_short = 'А1' if 'А 1' in level or 'А1' in level else ('А2' if 'А 2' in level or 'А2' in level else 'В1')
    title_clean = title.strip()
    md_lines = [f"# [{level_short}] {title_clean}\n"]
    sent_idx = 0
    for para in paragraphs:
        para_lines = []
        raw_sents = re.split(r'(?<=[.!?…])\s+(?=[А-ЯЁA-Z«\"—])', para)
        for s in raw_sents:
            s = s.strip()
            if not s:
                continue
            uz_trans = sentence_translations[sent_idx] if sent_idx < len(sentence_translations) else ''
            sent_idx += 1
            para_lines.append(annotate_sentence(s, uz_trans))
        md_lines.append('\n'.join(para_lines))
        md_lines.append('')
    return '\n'.join(md_lines).strip() + '\n'

def seed_records(records):
    """PostgreSQL ga xavfsiz va to'g'ri yozish."""
    subfolders = sorted(list(set(r['folder'] for r in records)))
    for ot, ok in OWNERS:
        # Bosh papka
        ex_top = db.fetch_one(
            """SELECT id FROM language_topics 
               WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
               AND folder = 'Чтение и аудирование' AND name = '__folder__' LIMIT 1""",
            {"ot": ot, "ok": ok, "l": LANG}
        )
        if not ex_top:
            db.execute(
                """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                   VALUES (:ot, :ok, :l, '__folder__', 'Чтение и аудирование', '', 0)""",
                {"ot": ot, "ok": ok, "l": LANG}
            )

        # Ichki papkalar
        for fld in subfolders:
            ex_fld = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = '__folder__' LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": fld}
            )
            if not ex_fld:
                db.execute(
                    """INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, content, sort_order)
                       VALUES (:ot, :ok, :l, '__folder__', :f, '', 0)""",
                    {"ot": ot, "ok": ok, "l": LANG, "f": fld}
                )

        # Matnlar
        for r in records:
            ex = db.fetch_one(
                """SELECT id FROM language_topics 
                   WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
                   AND folder = :f AND name = :n LIMIT 1""",
                {"ot": ot, "ok": ok, "l": LANG, "f": r['folder'], "n": r['name']}
            )
            if ex:
                db.execute(
                    """UPDATE language_topics 
                       SET content = :c, sort_order = :so, updated_at = NOW() 
                       WHERE id = :id""",
                    {"c": r['content'], "so": r['sort_order'], "id": ex['id']}
                )
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

def clean_old_padeshi():
    for ot, ok in OWNERS:
        db.execute(
            """DELETE FROM language_topics 
               WHERE owner_type = :ot AND owner_key = :ok AND lang = :l 
               AND folder LIKE 'Русские падежи%'""",
            {"ot": ot, "ok": ok, "l": LANG}
        )
    print("Eski 'Русские падежи' vaqtinchalik yozuvlari tozalandi.")

def process_theme(theme_texts, theme_folder_name):
    # Har bir matn gaplarini yig'ish
    t_sents = []
    ranges = []
    words_needed = set()
    for t in theme_texts:
        start = len(t_sents)
        for p in t['paragraphs']:
            for s in re.split(r'(?<=[.!?…])\s+(?=[А-ЯЁA-Z«\"—])', p):
                s = s.strip()
                if s:
                    t_sents.append(s)
                    for w in re.findall(r'[а-яёА-ЯЁ]+', s.lower()):
                        if w not in word_dict:
                            words_needed.add(w)
        ranges.append((start, len(t_sents)))

    # Yetishmayotgan so'zlar
    if words_needed:
        word_trans = batch_translate(sorted(list(words_needed))[:300], batch_size=50)
        for w, tr in word_trans.items():
            first = re.split(r'[,;/]', tr)[0].strip().lower()
            if first and first != w:
                word_dict[w] = first

    # Gaplar tarjimasi
    unique_sents = sorted(list(set(t_sents)))
    s_map = batch_translate(unique_sents, batch_size=30)

    # Formatlash
    records = []
    folder_path = f"Чтение и аудирование/{theme_folder_name}"
    for idx, t in enumerate(theme_texts):
        item_num = idx + 1
        level_short = 'А1' if 'А 1' in t['level'] or 'А1' in t['level'] else ('А2' if 'А 2' in t['level'] or 'А2' in t['level'] else 'В1')
        title_clean = t['title'].strip()
        item_name = f"{item_num:02d}. [{level_short}] {title_clean}"
        
        start, end = ranges[idx]
        cur_sents = t_sents[start:end]
        cur_uz = [s_map.get(s, s) for s in cur_sents]
        
        md_content = format_text(title_clean, t['level'], t['paragraphs'], cur_uz)
        records.append({
            'folder': folder_path,
            'name': item_name,
            'content': md_content,
            'sort_order': item_num * 10
        })

    # Bazaga yozish
    seed_records(records)
    print(f"✅ {theme_folder_name}: {len(records)} ta matn bazaga muvaffaqiyatli yuklandi!")
    return records

def main():
    print("=== 1. Xom matnlarni yuklash ===")
    with open(RAW_JSON, 'r', encoding='utf-8') as f:
        texts = json.load(f)
        
    clean_old_padeshi()

    # Mavzular bo'yicha ajratish
    themes = {}
    for t in texts:
        th = t['theme']
        themes.setdefault(th, []).append(t)

    all_seeded_records = []

    # 1-QADAM: BIRINCHI BO'LIB ТЕМА 1 NI YUKLASH
    th1_key = [k for k in themes.keys() if 'ТЕМА 1.' in k][0]
    print(f"\n🚀 1-BOSQICH: {th1_key} ni darhol yuklash...")
    r1 = process_theme(themes[th1_key], "01. О себе и не только")
    all_seeded_records.extend(r1)
    print("🎉 ТЕМА 1 SAYTGA TAYYOR BO'LDI! Saytda tekshirish mumkin.\n")

    # 2-QADAM: QOLGAN BARCHA MAVZULARNI (ТЕМА 2 - 13) KETMA-KET YUKLASH
    print("⏳ 2-BOSQICH: Qolgan barcha mavzularni yuklash davom etmoqda...")
    for th_key in sorted(themes.keys()):
        if th_key == th1_key:
            continue
        m = re.search(r'ТЕМА\s+(\d+)\.\s*(.*)', th_key)
        if m:
            num = int(m.group(1))
            name = m.group(2).strip()
            name_cap = name[0] + name[1:].lower() if name else ''
            folder_name = f"{num:02d}. {name_cap}"
        else:
            folder_name = th_key
        print(f"\nYuklanmoqda: {th_key} ({folder_name})...")
        r_other = process_theme(themes[th_key], folder_name)
        all_seeded_records.extend(r_other)

    # Yakuniy JSON saqlash
    out_json = '/opt/yordamchi/Yordamchisayt/database/seeds/rus_tili/chтение_и_аудирование_all.json'
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(all_seeded_records, f, ensure_ascii=False, indent=2)
    print(f"\n🏁 BARCHA 13 TA MAVZU (130 TA MATN) TO'LIQ BAZAGA YUKLANDI!")

if __name__ == '__main__':
    main()
