# -*- coding: utf-8 -*-
"""
Шумская Л.М., Билютенко Е.И. «Чтение и аудирование» kitobidagi barcha 130 ta matnni
yordamchi-sayt interactive reading (ru_reading) formatida yaratish va o'zbekcha tarjimalari bilan boyitish.
"""

import os
import sys
import fitz
import re
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

PDF_PATH = '/home/shamsiddin/Documents/shamsiyev/Rus tili/kitob/Чтение_и_аудирование,_Шумская_Л_М_,_Билютенко_Е_И_.pdf'
TOC_PATH = '/tmp/book_toc.txt'
SEEDS_DIR = '/home/shamsiddin/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/database/seeds/rus_tili/chтение_и_аудирование'
DOCS_DIR = '/home/shamsiddin/Documents/shamsiyev/Rus tili/kitob/chтение_и_аудирование'
CACHE_FILE = '/home/shamsiddin/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/database/seeds/rus_tili/translation_cache.json'
SLOVAR_FILE = '/home/shamsiddin/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/database/seeds/slovar_5000_words.json'

os.makedirs(SEEDS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# 1. Load Translation Cache
trans_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            trans_cache = json.load(f)
        print(f"Loaded {len(trans_cache)} cached translations.")
    except Exception as e:
        print(f"Error loading cache: {e}")

# 2. Predefined high-accuracy word & preposition mapping
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

# 3. Load 5000-word dictionary
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
        print(f"Dictionary expanded to {len(word_dict)} entries.")
    except Exception as e:
        print(f"Error reading dictionary: {e}")

def translate_gt(text):
    text = text.strip()
    if not text:
        return ''
    clean_ru = re.sub(r'[\u0300-\u036f]', '', text)
    if clean_ru in trans_cache:
        return trans_cache[clean_ru]
    
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=uz&dt=t&q=' + urllib.parse.quote(clean_ru)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(3):
        try:
            res = urllib.request.urlopen(req, timeout=8)
            data = json.loads(res.read().decode('utf-8'))
            trans = ''.join([part[0] for part in data[0] if part[0]])
            trans_cache[clean_ru] = trans
            return trans
        except Exception:
            time.sleep(0.3 * (attempt + 1))
    return clean_ru

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(trans_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def normalize_key(s):
    s = re.sub(r'[\u0300-\u036f]', '', s)
    s = re.sub(r'[^а-яёa-z0-9]+', '', s.lower())
    return s

def annotate_sentence(sent_ru, sent_uz):
    tokens = re.findall(r'[а-яёА-ЯЁa-zA-Z\u0300-\u036f]+|[^\s\w\u0300-\u036f]+|\s+', sent_ru)
    annotated = []
    
    for tok in tokens:
        clean_tok = re.sub(r'[\u0300-\u036f]', '', tok).strip().lower()
        if re.match(r'^[а-яёА-ЯЁa-zA-Z]+$', clean_tok):
            uz_trans = word_dict.get(clean_tok)
            if not uz_trans:
                uz_trans = translate_gt(clean_tok)
                if uz_trans and uz_trans.lower() != clean_tok:
                    word_dict[clean_tok] = uz_trans
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
    for pi, para in enumerate(paragraphs):
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

def main():
    print("=== 1. Extracting texts from PDF ===")
    doc = fitz.open(PDF_PATH)
    with open(TOC_PATH, encoding='utf-8') as f:
        toc_lines = f.readlines()

    current_theme = ''
    current_level = ''
    entries = []

    for line in toc_lines:
        line = line.strip()
        if not line:
            continue
        m_theme = re.search(r'(ТЕМА\s+\d+\.\s*[^…]+)', line)
        if m_theme:
            current_theme = re.sub(r'[…\.\s]+$', '', m_theme.group(1)).strip()
            continue
        m_level = re.search(r'(Уровень\s+[А-ЯA-Z]\s*\d*)', line)
        if m_level:
            current_level = m_level.group(1).strip()
            continue
        m_entry = re.search(r'^([А-ЯЁ\s\-\,\!\?\:\–\«\»\(\)\[\]\d]+)[…\.]+\s*(\d+)', line)
        if m_entry:
            title = m_entry.group(1).strip()
            page = int(m_entry.group(2))
            title_clean = re.sub(r'\s*\[\d+\]\s*', '', title).strip()
            if title_clean not in ['ПРЕДИСЛОВИЕ', 'УСЛОВНЫЕ ОБОЗНАЧЕНИЯ', 'ИСПОЛЬЗОВАННАЯ ЛИТЕРАТУРА']:
                entries.append({
                    'theme': current_theme,
                    'level': current_level,
                    'title': title_clean,
                    'page': page
                })

    all_blocks = []
    for p in range(3, 95):
        page_blocks = doc[p].get_text('blocks')
        for b in page_blocks:
            txt = b[4].strip()
            if not txt:
                continue
            if re.match(r'^(Авторы-составители|ЧТЕНИЕ И АУДИРОВАНИЕ|~\d+~)', txt):
                continue
            all_blocks.append({
                'page': p + 1,
                'text': txt,
                'bbox': b[:4]
            })

    title_blocks = []
    for idx, e in enumerate(entries):
        t_norm = normalize_key(e['title'])
        prev_b = title_blocks[-1]['block_idx'] if title_blocks else -1
        found_idx = -1
        
        for bi in range(prev_b + 1, len(all_blocks)):
            b_txt = all_blocks[bi]['text']
            lines = [l.strip() for l in b_txt.split('\n') if l.strip()]
            matched = False
            for l in lines:
                l_norm = normalize_key(l)
                if l_norm == t_norm or (len(l_norm) > 4 and len(l) < 70 and (t_norm.startswith(l_norm) or l_norm.startswith(t_norm))):
                    matched = True
                    break
            if matched:
                found_idx = bi
                break
                
        title_blocks.append({
            'entry': e,
            'block_idx': found_idx,
        })

    parsed_texts = []
    for i in range(len(title_blocks)):
        cur = title_blocks[i]
        next_b = title_blocks[i+1]['block_idx'] if i + 1 < len(title_blocks) else len(all_blocks)
        
        cur_b_idx = cur['block_idx']
        cur_block_text = all_blocks[cur_b_idx]['text']
        lines = [l.strip() for l in cur_block_text.split('\n') if l.strip()]
        
        t_norm = normalize_key(cur['entry']['title'])
        title_line_idx = -1
        for li, l in enumerate(lines):
            l_norm = normalize_key(l)
            if l_norm == t_norm or (len(l_norm) > 4 and len(l) < 70 and (t_norm.startswith(l_norm) or l_norm.startswith(t_norm))):
                title_line_idx = li
                break
                
        paragraphs = []
        if title_line_idx != -1 and title_line_idx + 1 < len(lines):
            p1 = ' '.join(lines[title_line_idx+1:])
            paragraphs.append(p1)
            
        for bi in range(cur_b_idx + 1, next_b):
            btxt = all_blocks[bi]['text'].strip()
            if re.match(r'^(ТЕМА\s+\d+|УРОВЕНЬ\s+[А-ЯA-Z]|Уровень\s+[А-ЯA-Z])', btxt, re.IGNORECASE):
                continue
            cleaned_para = re.sub(r'\s+', ' ', btxt)
            
            if paragraphs and not re.search(r'[.!?…»"\)]\s*$', paragraphs[-1]) and (cleaned_para and (cleaned_para[0].islower() or not cleaned_para[0].isupper())):
                paragraphs[-1] = paragraphs[-1] + ' ' + cleaned_para
            else:
                paragraphs.append(cleaned_para)
                
        parsed_texts.append({
            'theme': cur['entry']['theme'],
            'level': cur['entry']['level'],
            'title': cur['entry']['title'],
            'page': cur['entry']['page'],
            'paragraphs': paragraphs
        })

    print(f"Extracted {len(parsed_texts)} texts.")

    # Collect unique sentences across all texts
    all_sentences_list = []
    text_sentence_slices = []
    for t in parsed_texts:
        t_sents = []
        for p in t['paragraphs']:
            raw_sents = re.split(r'(?<=[.!?…])\s+(?=[А-ЯЁA-Z«\"—])', p)
            for s in raw_sents:
                s = s.strip()
                if s:
                    t_sents.append(s)
        start_idx = len(all_sentences_list)
        all_sentences_list.extend(t_sents)
        text_sentence_slices.append((start_idx, len(all_sentences_list)))

    print(f"Total sentences across 130 texts: {len(all_sentences_list)}")

    # Missing sentence translations
    missing_sents = [s for s in all_sentences_list if re.sub(r'[\u0300-\u036f]', '', s) not in trans_cache]
    print(f"Sentences to translate: {len(missing_sents)} (already cached: {len(all_sentences_list) - len(missing_sents)})")

    if missing_sents:
        print("Translating missing sentences in parallel...")
        unique_missing = list(set(missing_sents))
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(translate_gt, unique_missing))
        t1 = time.time()
        print(f"Translated {len(unique_missing)} unique sentences in {t1 - t0:.2f}s.")
        save_cache()

    # Pre-translate sentence list
    all_translated = [translate_gt(s) for s in all_sentences_list]
    save_cache()

    print("=== 2. Assembling interactive markdown texts ===")
    theme_folder_map = {}
    theme_names = []
    for t in parsed_texts:
        if t['theme'] not in theme_names:
            theme_names.append(t['theme'])

    for i, th in enumerate(theme_names):
        m = re.search(r'ТЕМА\s+(\d+)\.\s*(.*)', th)
        if m:
            num = int(m.group(1))
            name = m.group(2).strip()
            name_cap = name[0] + name[1:].lower() if name else ''
            theme_folder_map[th] = f"{num:02d}. {name_cap}"
        else:
            theme_folder_map[th] = f"{i+1:02d}. {th}"

    theme_counters = {}
    assembled_records = []

    for i, t in enumerate(parsed_texts):
        th = t['theme']
        subfolder_name = theme_folder_map[th]
        theme_counters[th] = theme_counters.get(th, 0) + 1
        item_num = theme_counters[th]
        
        level_short = 'А1' if 'А 1' in t['level'] or 'А1' in t['level'] else ('А2' if 'А 2' in t['level'] or 'А2' in level else 'В1')
        title_clean = t['title'].strip()
        item_name = f"{item_num:02d}. [{level_short}] {title_clean}"
        
        folder_path = f"Чтение и аудирование/{subfolder_name}"
        
        s_start, s_end = text_sentence_slices[i]
        s_trans = all_translated[s_start:s_end]
        
        md_content = format_text(title_clean, t['level'], t['paragraphs'], s_trans)
        
        # Save to seeds dir
        sub_seed_dir = os.path.join(SEEDS_DIR, subfolder_name)
        sub_doc_dir = os.path.join(DOCS_DIR, subfolder_name)
        os.makedirs(sub_seed_dir, exist_ok=True)
        os.makedirs(sub_doc_dir, exist_ok=True)
        
        # Sanitize filename
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title_clean)
        filename = f"{item_num:02d}. [{level_short}] {safe_title}.md"
        
        with open(os.path.join(sub_seed_dir, filename), 'w', encoding='utf-8') as f:
            f.write(md_content)
        with open(os.path.join(sub_doc_dir, filename), 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        assembled_records.append({
            'folder': folder_path,
            'name': item_name,
            'content': md_content,
            'sort_order': item_num * 10
        })

    # Save all data as JSON for database seeding
    data_json_path = os.path.join(SEEDS_DIR, 'chтение_и_аудирование_all.json')
    with open(data_json_path, 'w', encoding='utf-8') as f:
        json.dump(assembled_records, f, ensure_ascii=False, indent=2)

    save_cache()
    print(f"\nSUCCESS! Generated {len(assembled_records)} markdown files across 13 themes.")
    print(f"Data package saved to: {data_json_path}")

if __name__ == '__main__':
    main()
