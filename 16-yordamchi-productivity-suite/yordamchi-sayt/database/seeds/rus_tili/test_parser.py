# -*- coding: utf-8 -*-
import fitz
import re
import json

doc = fitz.open('/home/shamsiddin/Documents/shamsiyev/Rus tili/kitob/Чтение_и_аудирование,_Шумская_Л_М_,_Билютенко_Е_И_.pdf')

with open('/tmp/book_toc.txt', encoding='utf-8') as f:
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

def normalize(s):
    s = re.sub(r'[\u0300-\u036f]', '', s)
    s = re.sub(r'[^а-яёa-z0-9]+', '', s.lower())
    return s

title_blocks = []
for idx, e in enumerate(entries):
    t_norm = normalize(e['title'])
    prev_b = title_blocks[-1]['block_idx'] if title_blocks else -1
    found_idx = -1
    
    for bi in range(prev_b + 1, len(all_blocks)):
        b_txt = all_blocks[bi]['text']
        lines = [l.strip() for l in b_txt.split('\n') if l.strip()]
        matched = False
        for l in lines:
            l_norm = normalize(l)
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
    
    t_norm = normalize(cur['entry']['title'])
    title_line_idx = -1
    for li, l in enumerate(lines):
        l_norm = normalize(l)
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
        'paragraphs': paragraphs,
        'para_count': len(paragraphs)
    })

print(f"Parsed {len(parsed_texts)} texts.")
para_counts = [t['para_count'] for t in parsed_texts]
print(f"Min paragraphs: {min(para_counts)}, Max paragraphs: {max(para_counts)}, Avg: {sum(para_counts)//len(para_counts)}")
zero_paras = [t for t in parsed_texts if t['para_count'] == 0]
print(f"Zero paragraphs: {len(zero_paras)}")
for t in parsed_texts[:6]:
    print(f"[{t['level']}] {t['title']} -> {t['para_count']} paras:")
    for pi, p in enumerate(t['paragraphs'][:2]):
        print(f"   P{pi+1}: {p[:70]}...")
