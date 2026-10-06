"""Hujjat generatsiya xizmati — AI + fayllar.

Kichik ishlar (10 betgacha) bitta AI chaqiruv bilan yoziladi.
Katta ishlar bo'laklab: mundarija+kirish → har bob → xulosa+adabiyotlar,
har bob o'lchab-to'ldiriladi (90% dan qisqa bo'lsa chuqurlashtiriladi).

Qo'shimcha:
  - Navbat: bir vaqtda faqat BITTA generatsiya (zaif server himoyasi)
  - progress callback — Telegram xabarini jonli yangilash uchun
  - Premium tarif — kuchliroq model (details['tier'] == 'premium')
  - Web search — adabiyotlar va tahliliy boblar uchun haqiqiy manbalar
  - Titul varag'i meta — referat/mustaqil/kurs/diplom uchun kod bilan yasaladi
"""
from __future__ import annotations
import asyncio
import os
import re
import logging
from ai import provider as ai
from ai import prompts
from config import settings, DOC_TYPES

logger = logging.getLogger(__name__)

# ─── AI izohini (preamble) va gorizontal chiziqlarni tozalash ───
# Web-search yoki oddiy generatsiyada AI ba'zan hujjat oldidan o'ziga gapiradi:
# "Yetarli ma'lumot to'plandi", "Endi yozamiz", "Hujjat N so'zdan iborat" — bular
# hujjatga sizmasin. "---" ajratgichlar ham literal chiqmasin.
_HRULE = re.compile(r"^[\-*_—–=\s]{3,}$")
_META = [re.compile(p, re.I) for p in (
    r"yetarli\s+ma'?lumot",
    r"\bendi\b.{0,30}(yoz|tayyorla|boshla|o'?tam|davom|shakllantir)",
    r"hujjat.{0,25}so'?z(dan)?\s+iborat",
    r"\bso'?z\s+son",
    r"talab\s+qiling",
    r"qidiruv.{0,25}(natija|orqali|yakun|topdim|qilib|tugad|amalga)",
    r"web[\s-]?search|internetdan\s+(top|qidir|izla)",
    r"^\s*mana\b",
    r"^\s*quyida\b(?!.{0,3}(keltiril|ko'rsatil))",  # "quyidagi jadval" kabi legit emas
    r"^\s*(xo'?p|albatta|zo'r)\b",
    r"^\s*men\s+.{0,60}(yoz|tayyorla|beraman|boshla|qidir)",
    r"tayyorladim|yozib\s+beraman|yozib\s+bo'?ldim|yozib\s+chiqaman",
    r"^\s*(here|now|let me|i'?ll|i will)\b",
)]


def _strip_ai_meta(text: str) -> str:
    """AI ning kirish izohini va gorizontal chiziqlarni olib tashlaydi."""
    if not text:
        return text
    lines = [l for l in text.split("\n") if not _HRULE.fullmatch(l.strip())]
    out, started = [], False
    for l in lines:
        s = l.strip()
        if not started:
            if not s:
                continue
            if (s[0] in "#|" or s.startswith("**") or s.startswith("UDK")
                    or s.startswith("```") or s.startswith("$$")):
                started = True
            elif any(m.search(s) for m in _META):
                continue  # kirish izohi — tashlab yuboramiz
            else:
                started = True
        out.append(l)
    return "\n".join(out).strip("\n")

# 1 bet ≈ 300 so'z; o'zbek matni ~3 token/so'z → ~1000 token/bet
_TOKENS_PER_PAGE = 1000
_WORDS_PER_PAGE = 300
# Shu betdan boshlab hujjat bo'laklab yoziladi
_CHUNK_MIN_PAGES = 10

# Titul varag'i yasaladigan turlar
_TITLE_PAGE_TYPES = {
    "referat": "REFERAT",
    "mustaqil": "MUSTAQIL ISH",
    "kurs": "KURS ISHI",
    "diplom": "BITIRUV MALAKAVIY ISHI",
}

# Navbat: bitta-bitta generatsiya
_GEN_SEM = asyncio.Semaphore(1)
_WAITING = 0


def queue_size() -> int:
    """Hozir navbatda kutayotganlar soni."""
    return _WAITING


def _tmp(order_id: int, ext: str) -> str:
    os.makedirs(settings.tmp_dir, exist_ok=True)
    return os.path.join(settings.tmp_dir, f"{order_id}.{ext}")


def _tokens_for_pages(pages: float, extra: int = 1500) -> int:
    return max(3000, min(int(pages * _TOKENS_PER_PAGE) + extra, 32000))


async def _notify(progress, text: str):
    if progress:
        try:
            await progress(text)
        except Exception:
            pass


def _title_meta(doc_type: str, topic: str, language: str, details: dict,
                subject: str, author: str, group: str, supervisor: str) -> dict | None:
    label = _TITLE_PAGE_TYPES.get(doc_type)
    if not label:
        return None
    return {
        "doc_label": label,
        "topic": topic,
        "language": language,
        "otm": details.get("otm", ""),
        "fan": subject,
        "author": author,
        "group": group,
        "supervisor": supervisor,
    }


async def generate_document(order_id: int, data: dict,
                            progress=None) -> tuple[str, str, str, str]:
    """(file_path, file_format, provider, source_text) qaytaradi.

    Bir vaqtda faqat bitta generatsiya — qolganlari navbatda kutadi.
    Kutayotgan foydalanuvchiga darhol o'rni haqida xabar beriladi.
    """
    global _WAITING
    _WAITING += 1
    acquired = False
    if _GEN_SEM.locked():
        await _notify(progress,
                      f"👥 Navbatdasiz: {_WAITING}-o'rin. Ma'lumotlaringiz qabul qilindi — "
                      f"navbatingiz yetishi bilan avtomatik boshlanadi, hech narsa "
                      f"bosish shart emas.")
    try:
        async with _GEN_SEM:
            _WAITING = max(0, _WAITING - 1)
            acquired = True
            # Timeout — osilgan AI chaqiruvi butun navbatni to'xtatmasin.
            # Hujjat hajmiga qarab 8-25 daqiqa.
            pages = data.get("page_count", 10)
            limit = 480 if data["doc_type"] == "diplom" else (
                360 if pages >= 20 else (240 if pages >= 10 else 150))
            return await asyncio.wait_for(
                _generate(order_id, data, progress), timeout=limit)
    finally:
        if not acquired:
            _WAITING = max(0, _WAITING - 1)


async def _generate(order_id: int, data: dict, progress) -> tuple[str, str, str, str]:
    doc_type = data["doc_type"]
    topic = data.get("topic", "")
    details = data.get("details", {})
    language = data.get("language", "uz")
    page_count = data.get("page_count", 10)
    fmt = data.get("file_format", "docx")

    # Prompt va ma'lumotlarni tayyorlash
    subject = details.get("fan", details.get("subject", "—"))
    author = (details.get("talaba", details.get("muallif", details.get("author", "Talaba"))))
    group = details.get("guruh", details.get("group", "—"))
    supervisor = details.get("rahbar", details.get("ilmiy rahbar", "—"))
    model = settings.claude_model_premium if details.get("tier") == "premium" else None
    web = settings.web_search_on() and doc_type not in ("slayd", "krasword")

    # AI chaqiruv
    if doc_type == "slayd":
        await _notify(progress, "📊 Slaydlar rejasi tuzilmoqda...")
        sys_p, user_p = prompts.slayd(topic, subject, author, page_count, language)
        # Har slayd ~450-600 token (chart/two_col maketlar ko'proq joy oladi)
        max_tok = max(5000, min(page_count * 600 + 2500, 28000))
        text, prov = await ai.generate_json(sys_p, user_p, max_tokens=max_tok, model=model)

    elif doc_type == "krasword":
        await _notify(progress, "🎯 Krossvord so'zlari tanlanmoqda...")
        sys_p, user_p = prompts.krasword(topic, language, count=page_count)
        max_tok = max(2500, min(page_count * 60 + 1000, 6000))
        text, prov = await ai.generate_json(sys_p, user_p, max_tokens=max_tok, model=model)

    elif prompts.chunkable(doc_type) and page_count >= _CHUNK_MIN_PAGES:
        text, prov = await _generate_chunked(
            doc_type, topic, subject, author, group, supervisor,
            language, page_count, model, web, progress)

    else:
        await _notify(progress, "✍️ Hujjat yozilmoqda...")
        if doc_type == "tezis":
            sys_p, user_p = prompts.tezis(topic, subject, author, language)
            max_tok = 6000
        elif doc_type == "mustaqil":
            sys_p, user_p = prompts.mustaqil(topic, subject, author, group, language, page_count)
            max_tok = _tokens_for_pages(page_count)
        elif doc_type == "referat":
            sys_p, user_p = prompts.referat(topic, subject, author, group, language, page_count)
            max_tok = _tokens_for_pages(page_count)
        elif doc_type == "maqola":
            sys_p, user_p = prompts.maqola(topic, subject, author, language, page_count)
            max_tok = _tokens_for_pages(page_count)
        elif doc_type == "kurs":
            sys_p, user_p = prompts.kurs_ishi(topic, subject, author, group,
                                              supervisor, language, page_count)
            max_tok = _tokens_for_pages(page_count)
        elif doc_type == "diplom":
            sys_p, user_p = prompts.diplom(topic, subject, author, group,
                                           supervisor, language, page_count)
            max_tok = _tokens_for_pages(page_count)
        else:
            raise ValueError(f"Noma'lum doc_type: {doc_type}")
        if web:
            text, prov = await ai.generate_with_search(
                sys_p, user_p + "\n" + prompts.SEARCH_NOTE,
                max_tokens=max_tok, model=model, max_searches=3)
        else:
            text, prov = await ai.generate(sys_p, user_p, max_tokens=max_tok, model=model)
        text = _strip_ai_meta(text)

    # Fayl yaratish
    await _notify(progress, "📄 Fayl tayyorlanmoqda...")
    meta = _title_meta(doc_type, topic, language, details,
                       subject, author, group, supervisor)

    if doc_type == "slayd":
        from docs.pptx_builder import parse_slides, fetch_images_for_slides, build_pptx
        slides = parse_slides(text)
        if len(slides) < 3:
            raise ValueError(
                f"Slayd ma'lumotlari yetarli emas ({len(slides)} ta) — AI javobi buzuq/kesilgan")
        await _notify(progress, "🖼 Rasmlar va grafiklar tayyorlanmoqda...")
        images = await fetch_images_for_slides(slides)
        path = _tmp(order_id, "pptx")
        build_pptx(slides, path, topic, author, subject if subject != "—" else "", images)
        return path, "pptx", prov, text

    elif doc_type == "krasword":
        from docs.crossword import build_crossword
        png = _tmp(order_id, "png")
        docx = _tmp(order_id, "docx")
        build_crossword(text, png, docx, topic)
        # Ikkalasini yuborish uchun png ni asosiy qilamiz (docx qo'shimcha)
        return png, "png", prov, text

    elif fmt == "pdf":
        # reportlab bilan to'g'ridan PDF (LibreOffice shart emas, kam RAM da ishlaydi)
        from docs.pdf_builder import build_pdf
        pdf_path = _tmp(order_id, "pdf")
        try:
            build_pdf(text, pdf_path, topic, meta=meta)
            return pdf_path, "pdf", prov, text
        except Exception as e:
            logger.warning("PDF yaratish muvaffaqiyatsiz: %s — DOCX qaytarilmoqda", e)
            from docs.docx_builder import build_docx
            docx_path = _tmp(order_id, "docx")
            build_docx(text, docx_path, topic, meta=meta)
            return docx_path, "docx", prov, text

    else:
        from docs.docx_builder import build_docx
        path = _tmp(order_id, "docx")
        build_docx(text, path, topic, meta=meta)
        return path, "docx", prov, text


async def rebuild_file(order_id: int, data: dict, text: str) -> tuple[str, str]:
    """Revizyondan keyin faylni qayta yasaydi. (path, fmt) qaytaradi."""
    doc_type = data["doc_type"]
    topic = data.get("topic", "")
    details = data.get("details", {})
    language = data.get("language", "uz")
    fmt = data.get("file_format", "docx")
    subject = details.get("fan", details.get("subject", "—"))
    author = (details.get("talaba", details.get("muallif", details.get("author", "Talaba"))))
    group = details.get("guruh", details.get("group", "—"))
    supervisor = details.get("rahbar", details.get("ilmiy rahbar", "—"))
    meta = _title_meta(doc_type, topic, language, details,
                       subject, author, group, supervisor)
    if fmt == "pdf":
        from docs.pdf_builder import build_pdf
        path = _tmp(order_id, "pdf")
        try:
            build_pdf(text, path, topic, meta=meta)
            return path, "pdf"
        except Exception:
            pass
    from docs.docx_builder import build_docx
    path = _tmp(order_id, "docx")
    build_docx(text, path, topic, meta=meta)
    return path, "docx"


async def _generate_chunked(doc_type: str, topic: str, subject: str, author: str,
                            group: str, supervisor: str, language: str,
                            pages: int, model: str | None, web: bool,
                            progress) -> tuple[str, str]:
    """Katta hujjatni qism-qism yozadi va birlashtiradi."""
    meta_lines = [f"Fan: {subject}", f"Talaba: {author}"]
    if group and group != "—":
        meta_lines.append(f"Guruh: {group}")
    if doc_type in ("kurs", "diplom") and supervisor and supervisor != "—":
        meta_lines.append(f"Ilmiy rahbar: {supervisor}")
    meta = "\n".join(meta_lines)

    plan = prompts.chunk_plan(doc_type, pages)
    total = len(plan)
    providers: list[str] = []
    parts: list[str] = []

    # 1) Mundarija + kirish
    await _notify(progress, f"📑 Reja va kirish yozilmoqda... (1/{total})")
    intro_pages = plan[0][1]
    sys_p, user_p = prompts.chunk_intro(doc_type, topic, meta, language, pages, intro_pages)
    intro, prov = await ai.generate(sys_p, user_p, model=model,
                                    max_tokens=_tokens_for_pages(intro_pages, extra=2000))
    intro = _strip_ai_meta(intro.strip())
    parts.append(intro)
    providers.append(prov)
    logger.info("Bo'lak 1/%s tayyor (intro, %s)", total, prov)

    # 2) Boblar — mundarijaga tayanib, birma-bir
    done_labels: list[str] = []
    for i, (label, part_pages) in enumerate(plan[1:-1], start=2):
        await _notify(progress, f"📝 {i - 1}-bob yozilmoqda... ({i}/{total})")
        sys_p, user_p = prompts.chunk_body(doc_type, topic, language, intro,
                                           label, part_pages, done_labels, subject)
        # Tahliliy boblarda web search (real statistika) — kurs/diplom/maqola
        use_search = web and done_labels and doc_type in ("kurs", "diplom", "maqola")
        if use_search:
            body, prov = await ai.generate_with_search(
                sys_p, user_p + "\n" + prompts.SEARCH_NOTE,
                max_tokens=_tokens_for_pages(part_pages), model=model, max_searches=3)
        else:
            body, prov = await ai.generate(sys_p, user_p, model=model,
                                           max_tokens=_tokens_for_pages(part_pages))
        body = _strip_ai_meta(body.strip())
        providers.append(prov)

        # O'lchab-to'ldirish: bob nishondan qisqa chiqsa, chuqurlashtiramiz.
        # Nishon prompt bilan bir xil (prompts._w — kalibrlangan matn hajmi).
        target = prompts._w(part_pages)
        got = len(body.split())
        if got < int(target * 0.9):
            add = target - got
            sys_e, user_e = prompts.chunk_extend(doc_type, topic, language,
                                                 label, body, add, subject)
            extra, prov_e = await ai.generate(
                sys_e, user_e, model=model,
                max_tokens=_tokens_for_pages(add / _WORDS_PER_PAGE, extra=1000))
            body = body + "\n\n" + _strip_ai_meta(extra.strip())
            providers.append(prov_e)
            logger.info("Bo'lak %s to'ldirildi: %s → %s so'z (nishon %s)",
                        i, got, len(body.split()), target)

        parts.append(body)
        done_labels.append(label)
        logger.info("Bo'lak %s/%s tayyor (%s, %s)", i, total, label[:30], prov)

    # 3) Xulosa + adabiyotlar (web search: haqiqiy manbalar)
    await _notify(progress, f"📚 Xulosa va adabiyotlar... ({total}/{total})")
    final_pages = plan[-1][1]
    sys_p, user_p = prompts.chunk_final(doc_type, topic, language, intro,
                                        final_pages, done_labels)
    if web:
        final, prov = await ai.generate_with_search(
            sys_p, user_p + "\n" + prompts.SEARCH_NOTE,
            max_tokens=_tokens_for_pages(final_pages), model=model, max_searches=4)
    else:
        final, prov = await ai.generate(sys_p, user_p, model=model,
                                        max_tokens=_tokens_for_pages(final_pages))
    parts.append(_strip_ai_meta(final.strip()))
    providers.append(prov)

    text = "\n\n".join(parts)
    provider = "claude" if all(p == "claude" for p in providers) else (
        "openai" if all(p == "openai" for p in providers) else "claude+openai")
    logger.info("Bo'laklab generatsiya yakunlandi: %s bet, ~%s so'z, provider=%s",
                pages, len(text.split()), provider)
    return text, provider
