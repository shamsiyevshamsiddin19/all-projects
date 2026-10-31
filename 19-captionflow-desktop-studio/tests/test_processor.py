"""desktop_processor uchun regressiya testlari.

Yangi bog'liqlik kerak emas — standart `unittest` bilan ishlaydi:

    .venv/bin/python -m unittest discover -s tests -v

Bu yerda tekshiriladigan mantiq jimgina buziladi: natija xato bermaydi,
shunchaki yomonlashadi (gap bo'linmaydi, teshik topilmaydi, lug'atga
yordamchi so'zlar to'lib ketadi). Shuning uchun har biriga qotirilgan misol.
"""
from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Paketning o'zi sinaladi; `desktop_processor.py` endi faqat kirish nuqtasi.
import subtitr as dp  # noqa: E402

# Ichki (pastki chiziqli) nomlar yulduzcha-import bilan kelmaydi, va
# monkeypatch nomni E'LON QILGAN modulga qo'yilishi kerak — aks holda
# funksiya o'z modulidagi eski nomni ko'raveradi.
from subtitr import cache as m_cache  # noqa: E402
from subtitr import documents as m_doc  # noqa: E402
from subtitr import clean as m_clean  # noqa: E402
from subtitr import media as m_media  # noqa: E402
from subtitr import translate as m_tx  # noqa: E402
from subtitr import vocab as m_vocab  # noqa: E402
from subtitr import pipeline as m_pipe  # noqa: E402
from subtitr import subtitles as m_sub  # noqa: E402
from subtitr import transcribe as m_tr  # noqa: E402


def seg(start: float, end: float, text: str) -> dp.Segment:
    return dp.Segment(start, end, text)


class LanguageCodeTests(unittest.TestCase):
    """Groq tilni "russian", lokal model "ru" deb qaytaradi."""

    def test_full_name_becomes_iso_code(self):
        self.assertEqual(dp.normalize_lang_code("russian"), "ru")
        self.assertEqual(dp.normalize_lang_code("Russian"), "ru")
        self.assertEqual(dp.normalize_lang_code("uzbek"), "uz")

    def test_code_passes_through(self):
        self.assertEqual(dp.normalize_lang_code("ru"), "ru")
        self.assertEqual(dp.normalize_lang_code("pt-BR"), "pt")

    def test_not_a_language_is_rejected(self):
        # Whisper ba'zan yozuv tizimini qaytaradi — bu til emas.
        self.assertEqual(dp.normalize_lang_code("latin"), "")
        self.assertEqual(dp.normalize_lang_code(""), "")
        self.assertEqual(dp.normalize_lang_code("auto"), "")

    def test_helpers_found_for_groq_language_name(self):
        lang = dp.normalize_lang_code("russian")
        self.assertEqual(dp.helper_category("что", lang), "conjunction")
        self.assertEqual(dp.helper_category("на", lang), "preposition")
        self.assertEqual(dp.helper_category("я", lang), "pronoun")
        self.assertEqual(dp.helper_category("не", lang), "particle")

    def test_inflected_form_is_caught_through_its_lemma(self):
        """Har bir kelishik shaklini ro'yxatga yozib bo'lmaydi.

        "тобой" ro'yxatda yo'q, lekin lemmasi "ты" — olmosh. Lemma
        qaralmasa, u lug'at tepasida qolib ketadi."""
        from subtitr.vocab import entry_helper
        entry = {"word": "тобой", "lemma": "ты", "translation": "sen bilan"}
        self.assertEqual(entry_helper(entry, "ru"), "pronoun")

    def test_content_word_keeps_its_place_despite_lemma(self):
        from subtitr.vocab import entry_helper
        entry = {"word": "ёлки", "lemma": "ёлка", "translation": "archa"}
        self.assertEqual(entry_helper(entry, "ru"), "")

    def test_content_words_are_not_helpers(self):
        lang = dp.normalize_lang_code("russian")
        for word in ("зима", "праздник", "украсить", "очень"):
            self.assertEqual(dp.helper_category(word, lang), "", word)


class CacheSignatureTests(unittest.TestCase):
    def test_signature_tracks_logic_version(self):
        """Kod yaxshilanganda eski kesh qaytarilib qolmasligi kerak."""
        before = dp.transcription_signature()
        original = m_cache.TRANSCRIPTION_LOGIC_VERSION
        try:
            m_cache.TRANSCRIPTION_LOGIC_VERSION = original + "x"
            self.assertNotEqual(before, dp.transcription_signature())
        finally:
            m_cache.TRANSCRIPTION_LOGIC_VERSION = original
        self.assertEqual(before, dp.transcription_signature())


class SentenceSplitTests(unittest.TestCase):
    def split(self, text: str) -> list[str]:
        return [text[a:b].strip() for a, b in m_doc._read_sentence_spans(text)]

    def test_basic_punctuation(self):
        self.assertEqual(
            self.split("Привет. Как дела? Хорошо!"),
            ["Привет.", "Как дела?", "Хорошо!"],
        )

    def test_abbreviation_does_not_split(self):
        self.assertEqual(
            self.split("Купили хлеб, молоко и т.д. Потом пошли домой."),
            ["Купили хлеб, молоко и т.д.", "Потом пошли домой."],
        )

    def test_initials_do_not_split(self):
        self.assertEqual(len(self.split("Это А. С. Пушкин. Он поэт.")), 2)

    def test_lowercase_after_dot_continues(self):
        self.assertEqual(len(self.split("Это т.д. и прочее")), 1)


class ImplicitBreakTests(unittest.TestCase):
    """Whisper gap oxiridagi nuqtani tez-tez tashlab ketadi."""

    def test_missing_period_detected(self):
        self.assertTrue(m_doc._read_implicit_break("Так я же дома", "Гена, я говорю"))

    def test_comma_means_sentence_continues(self):
        self.assertFalse(m_doc._read_implicit_break("Спасибо,", "Чебурашка"))

    def test_lowercase_next_means_continues(self):
        self.assertFalse(m_doc._read_implicit_break("Нужно украсить", "елку яркими"))

    def test_trailing_function_word_blocks_break(self):
        # "пошёл в" — gap albatta davom etadi, "Москву" bosh harfli bo'lsa ham.
        self.assertFalse(m_doc._read_implicit_break("Он пошёл в", "Москву"))

    def test_existing_period_is_left_alone(self):
        self.assertFalse(m_doc._read_implicit_break("Всё готово.", "Пошли"))


class ReadingBlockTests(unittest.TestCase):
    def test_pause_starts_new_paragraph(self):
        blocks = dp.build_reading_blocks([
            seg(0.0, 2.0, "Первое предложение здесь, оно довольно длинное."),
            seg(2.2, 4.0, "Второе рядом с ним."),
            seg(20.0, 22.0, "Это уже после долгой паузы."),
        ])
        self.assertEqual(len(blocks), 2)
        self.assertIn("Второе", blocks[0].text)
        self.assertTrue(blocks[1].text.startswith("Это уже"))

    def test_short_interjection_does_not_become_its_own_paragraph(self):
        blocks = dp.build_reading_blocks([
            seg(0.0, 1.0, "О!"),
            seg(10.0, 12.0, "Потом началась совсем другая сцена, и всё изменилось."),
        ])
        self.assertEqual(len(blocks), 1)

    def test_missing_period_is_repaired(self):
        blocks = dp.build_reading_blocks([
            seg(0.0, 2.0, "Так я же дома"),
            seg(2.0, 4.0, "Гена, я говорю про деревья"),
        ])
        self.assertIn("дома. Гена", blocks[0].text)

    def test_paragraph_ends_with_punctuation(self):
        blocks = dp.build_reading_blocks([seg(0.0, 2.0, "Без точки в конце")])
        self.assertTrue(blocks[0].text.endswith("."))

    def test_empty_input(self):
        self.assertEqual(dp.build_reading_blocks([]), [])


class SentencePairTests(unittest.TestCase):
    def test_multi_segment_sentence_keeps_translation_aligned(self):
        original = [
            seg(0.0, 2.0, "Нужно украсить елку"),
            seg(2.0, 4.0, "яркими игрушками."),
            seg(4.5, 6.0, "А у нас их нет."),
        ]
        translated = [
            seg(0.0, 2.0, "Yangi yil daraxtini bezash kerak"),
            seg(2.0, 4.0, "yorqin o'yinchoqlar bilan."),
            seg(4.5, 6.0, "Bizda ular yo'q."),
        ]
        pairs = dp.build_sentence_pairs(original, translated)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0].source, "Нужно украсить елку яркими игрушками.")
        self.assertEqual(
            pairs[0].target, "Yangi yil daraxtini bezash kerak yorqin o'yinchoqlar bilan."
        )
        self.assertEqual(pairs[1].target, "Bizda ular yo'q.")

    def test_without_translation_target_is_empty(self):
        pairs = dp.build_sentence_pairs([seg(0.0, 2.0, "Привет.")], None)
        self.assertEqual(pairs[0].target, "")


class VocabMarkingTests(unittest.TestCase):
    VOCAB = {
        "зима": ("qish", 3),
        "праздник": ("bayram", 1),
        "украсить": ("bezash", 1),
        "елку": ("archa", 2),
        "яркими": ("yorqin", 1),
    }

    def test_short_sentence_gets_one_mark(self):
        out = dp.mark_vocab_words("Зима и праздник.", self.VOCAB)
        self.assertEqual(out.count("{"), 1)

    def test_mark_count_scales_with_length(self):
        text = "Нужно украсить елку яркими игрушками, а зима и праздник рядом."
        out = dp.mark_vocab_words(text, self.VOCAB)
        self.assertGreaterEqual(out.count("{"), 2)
        self.assertLessEqual(out.count("{"), m_doc._READ_MD_MAX_MARKS)

    def test_punctuation_stays_outside_braces(self):
        out = dp.mark_vocab_words("Это праздник.", self.VOCAB)
        self.assertIn("{праздник|bayram}.", out)

    def test_skip_set_is_honoured(self):
        out = dp.mark_vocab_words("Это праздник.", self.VOCAB, skip={"праздник"})
        self.assertNotIn("{", out)

    def test_rarest_word_is_preferred(self):
        # "зима" 3 marta, "праздник" 1 marta uchraydi -> kam uchragani tanlanadi.
        out = dp.mark_vocab_words("Зима праздник.", self.VOCAB)
        self.assertIn("{праздник|bayram}", out)


class VocabMapTests(unittest.TestCase):
    def test_helper_words_are_dropped(self):
        entries = [{"word": "на", "translation": "ustida", "helper": "preposition", "count": 9}]
        self.assertEqual(dp.reading_vocab_map(entries), {})

    def test_transliteration_only_translation_is_dropped(self):
        # "Гена -> Gena" hech narsa o'rgatmaydi (ism yoki o'zlashma).
        entries = [
            {"word": "гена", "translation": "Gena", "helper": "", "count": 4},
            {"word": "радио", "translation": "radio", "helper": "", "count": 1},
        ]
        self.assertEqual(dp.reading_vocab_map(entries), {})

    def test_long_translation_is_dropped(self):
        entries = [{"word": "зима", "translation": "juda sovuq qor yog'adigan fasl",
                    "helper": "", "count": 1}]
        self.assertEqual(dp.reading_vocab_map(entries), {})

    def test_good_entry_kept(self):
        entries = [{"word": "зима", "translation": "qish", "helper": "", "count": 2}]
        self.assertEqual(dp.reading_vocab_map(entries), {"зима": ("qish", 2)})


class ProperNounTests(unittest.TestCase):
    def test_mid_sentence_capital_is_a_name(self):
        names = dp.reading_proper_nouns([
            "Гена, я говорю про деревья.",
            "Это замечательная идея, Чебурашка.",
        ])
        self.assertIn("чебурашка", names)

    def test_sentence_start_alone_is_not_a_name(self):
        names = dp.reading_proper_nouns(["Зима пришла."])
        self.assertNotIn("зима", names)


class GapDetectionTests(unittest.TestCase):
    """Groq butun bir parchani qaytarmasa, segmentlar orasida teshik qoladi."""

    def setUp(self):
        self._real = m_tr.speech_seconds

    def tearDown(self):
        m_tr.speech_seconds = self._real

    def test_hole_with_speech_is_found(self):
        m_tr.speech_seconds = lambda media, start, dur: dur * 0.5
        found = dp.swallowed_gap_ranges(
            Path("/dev/null"),
            [seg(0.0, 10.0, "a"), seg(30.0, 40.0, "b")],
            60.0,
        )
        self.assertIn((10.0, 30.0), found)
        self.assertIn((40.0, 60.0), found)  # oxiridagi teshik ham

    def test_silent_hole_is_skipped(self):
        m_tr.speech_seconds = lambda media, start, dur: 0.0
        found = dp.swallowed_gap_ranges(
            Path("/dev/null"), [seg(0.0, 10.0, "a"), seg(30.0, 40.0, "b")], 60.0
        )
        self.assertEqual(found, [])

    def test_short_gap_is_not_a_hole(self):
        m_tr.speech_seconds = lambda media, start, dur: dur
        found = dp.swallowed_gap_ranges(
            Path("/dev/null"), [seg(0.0, 10.0, "a"), seg(11.0, 20.0, "b")], 20.0
        )
        self.assertEqual(found, [])

    def test_old_logic_alone_misses_holes(self):
        """`suspect_ranges` faqat mavjud segment ICHIGA qaraydi.

        Segmentlarning o'zi normal (matni zich) bo'lsa, ular orasidagi
        20 soniyalik teshikni eski mantiq umuman ko'rmaydi — bugungi
        tuzatishning sababi aynan shu."""
        dense = [
            seg(0.0, 10.0, "Это достаточно плотный текст для десяти секунд речи."),
            seg(30.0, 40.0, "И здесь тоже вполне обычная плотность текста есть."),
        ]
        self.assertEqual(dp.suspect_ranges(dense), [])
        m_tr.speech_seconds = lambda media, start, dur: dur * 0.5
        self.assertIn((10.0, 30.0), dp.swallowed_gap_ranges(Path("/dev/null"), dense, 40.0))


class RescanSelectionTests(unittest.TestCase):
    """Oynani to'liq qoplagan soxta qator haqiqiy qatorlarni siqib
    chiqarmasligi kerak (u matni uzun bo'lgani uchun tanlovda g'olib chiqib,
    keyin zichlik filtriga tushib tashlanardi — oraliq bo'sh qolardi)."""

    def setUp(self):
        self._gaps = m_tr.swallowed_gap_ranges
        self._one = m_tr._rescan_one
        self._emit = m_tr.emit
        m_tr.swallowed_gap_ranges = lambda media, segments, duration: [(10.0, 26.0)]
        m_tr.emit = lambda *a, **k: None   # test chiqishi toza qolsin

    def tearDown(self):
        m_tr.swallowed_gap_ranges = self._gaps
        m_tr._rescan_one = self._one
        m_tr.emit = self._emit

    def test_sparse_window_wide_candidate_does_not_win(self):
        sparse = seg(9.0, 21.0, "Нет, смотрит, нет, кот Вася смот")   # 12s, siyrak
        good_a = seg(12.0, 16.0, "Смотрит в шкафу? Нет.")
        good_b = seg(17.0, 21.0, "Кот Вася смотрит на бабушку.")

        def fake_one(transcribe, media, language, start, dur, tmp_dir):
            if start < 12.0:
                return [sparse, good_a], []
            return [good_b], []

        m_tr._rescan_one = fake_one
        out, _ = dp.rescan_swallowed_speech(
            lambda p, l, s: ([], [], ""), Path("/dev/null"), "ru",
            [seg(0.0, 10.0, "до"), seg(26.0, 30.0, "после")], [], None,
        )
        texts = [s.text for s in out]
        self.assertIn(good_a.text, texts)
        self.assertNotIn(sparse.text, texts)

    def test_originals_outside_the_hole_survive(self):
        m_tr._rescan_one = lambda *a, **k: ([seg(12.0, 16.0, "новое")], [])
        before = [seg(0.0, 10.0, "до"), seg(26.0, 30.0, "после")]
        out, _ = dp.rescan_swallowed_speech(
            lambda p, l, s: ([], [], ""), Path("/dev/null"), "ru", before, [], None,
        )
        texts = [s.text for s in out]
        self.assertIn("до", texts)
        self.assertIn("после", texts)
        self.assertIn("новое", texts)

    def test_no_overlapping_segments(self):
        m_tr._rescan_one = lambda *a, **k: ([seg(12.0, 28.0, "новое")], [])
        out, _ = dp.rescan_swallowed_speech(
            lambda p, l, s: ([], [], ""), Path("/dev/null"), "ru",
            [seg(0.0, 10.0, "до"), seg(26.0, 30.0, "после")], [], None,
        )
        for cur, nxt in zip(out, out[1:]):
            self.assertLessEqual(cur.end, nxt.start + 1e-6)

    def test_kill_switch(self):
        import os
        m_tr._rescan_one = lambda *a, **k: ([seg(12.0, 16.0, "новое")], [])
        os.environ["SUBTITR_NO_RESCAN"] = "1"
        try:
            before = [seg(0.0, 10.0, "до")]
            out, _ = dp.rescan_swallowed_speech(
                lambda p, l, s: ([], [], ""), Path("/dev/null"), "ru", before, [], None,
            )
            self.assertEqual(out, before)
        finally:
            del os.environ["SUBTITR_NO_RESCAN"]


class MarkdownOutputTests(unittest.TestCase):
    """Yordamchi saytining "O'qish" formati."""

    def pairs(self):
        return dp.build_sentence_pairs(
            [seg(0.0, 2.0, "Зима пришла."), seg(2.2, 4.0, "Стало холодно."),
             seg(30.0, 32.0, "Потом наступила весна.")],
            [seg(0.0, 2.0, "Qish keldi."), seg(2.2, 4.0, "Sovuq bo'ldi."),
             seg(30.0, 32.0, "Keyin bahor keldi.")],
        )

    def write(self, vocab=None):
        tmp = Path(tempfile.mkdtemp()) / "out.md"
        dp.write_md_reading(tmp, "Sinov", self.pairs(), vocab or {})
        return tmp.read_text(encoding="utf-8")

    def test_title_and_pairs(self):
        text = self.write()
        lines = text.split("\n")
        self.assertEqual(lines[0], "# Sinov")
        self.assertIn("Зима пришла.", text)
        self.assertIn(":: Qish keldi.", text)

    def test_every_sentence_has_a_translation(self):
        body = [l for l in self.write().split("\n")[1:] if l.strip()]
        sources = [l for l in body if not l.startswith("::")]
        targets = [l for l in body if l.startswith(":: ")]
        self.assertEqual(len(sources), len(targets))

    def test_paragraph_break_uses_two_blank_lines(self):
        # Uzoq jimlikdan keyingi gap yangi xatboshi bo'ladi.
        self.assertIn("\n\n\nПотом наступила весна.", self.write())

    def test_no_bom(self):
        # Faylni sayt o'qiydi; BOM sarlavhani buzishi mumkin.
        self.assertFalse(self.write().startswith("﻿"))

    def test_format_characters_are_stripped_from_text(self):
        pairs = [dp.ReadingPair(0.0, 1.0, "Текст с {скобками} и | чертой.",
                                "Matn", False)]
        tmp = Path(tempfile.mkdtemp()) / "out.md"
        dp.write_md_reading(tmp, "T", pairs, {})
        body = tmp.read_text(encoding="utf-8").split("\n")[2]
        self.assertNotIn("{", body)
        self.assertNotIn("|", body)


class AssOutputTests(unittest.TestCase):
    def render(self, show_original: bool) -> list[str]:
        tmp = Path(tempfile.mkdtemp()) / "out.ass"
        dp.write_ass(
            tmp,
            [seg(0.0, 2.0, "Original")],
            [seg(0.0, 2.0, "Tarjima")],
            None, {}, 1920, 1080,
            trans_color="#39FF14", show_original=show_original,
        )
        return [l for l in tmp.read_text().splitlines() if l.startswith("Dialogue:")]

    def test_translation_only_has_a_single_line(self):
        lines = self.render(show_original=False)
        self.assertEqual(len(lines), 1)
        self.assertIn("Tarjima", lines[0])
        self.assertNotIn("Original", lines[0])

    def test_dual_keeps_both(self):
        joined = "\n".join(self.render(show_original=True))
        self.assertIn("Original", joined)
        self.assertIn("Tarjima", joined)

    def test_no_drop_shadow(self):
        """ASS soyasi — matnning surilgan qora nusxasi. Kontur bilan birga u
        harflarni ikkilantirib xiralashtiradi, shuning uchun 0 bo'lishi
        kerak (Shadow — uslub qatoridagi 17-maydon)."""
        tmp = Path(tempfile.mkdtemp()) / "out.ass"
        dp.write_ass(tmp, [seg(0.0, 2.0, "Matn")], None, None, {}, 1920, 1080)
        styles = [l for l in tmp.read_text().splitlines() if l.startswith("Style: ")]
        self.assertTrue(styles)
        for line in styles:
            shadow = line.split(",")[17]
            self.assertEqual(shadow.strip(), "0", line[:40])

    def test_outline_stays_thin_enough_to_read(self):
        """Kontur shrift balandligining ~6% i: fondan ajratadi, lekin
        harf ichini yopib qo'ymaydi (0.13 da aynan shunday bo'lgan edi)."""
        for w, h in ((1920, 1080), (1280, 720), (854, 480)):
            layout = dp.layout_for(w, h, dual=False)
            ratio = layout["outline"] / layout["font"]
            self.assertLessEqual(ratio, 0.10, f"{w}x{h}: kontur juda qalin")
            self.assertGreaterEqual(layout["outline"], 2, f"{w}x{h}: kontur juda ingichka")

    def test_solo_line_is_larger(self):
        solo = dp.layout_for(1920, 1080, dual=False)["font"]
        dual = dp.layout_for(1920, 1080, dual=True)["font"]
        self.assertGreater(solo, dual)


class PackageStructureTests(unittest.TestCase):
    """Kod modullarga bo'lingani uchun paydo bo'ladigan xatolar.

    Bular ish vaqtidagina ko'rinadi — pyflakes ham, import ham ushlamaydi."""

    PKG = Path(dp.__file__).parent

    def modules(self):
        for path in sorted(self.PKG.glob("*.py")):
            if path.name != "__init__.py":
                yield path, ast.parse(path.read_text(encoding="utf-8"))

    def test_global_names_live_in_their_own_module(self):
        """`global X` faqat O'Z modulining global nomiga qaraydi.

        X boshqa modulga ko'chib qolsa, funksiya uni ko'rmaydi va
        NameError beradi — `_JS_RUNTIME_CACHE` bilan aynan shunday
        bo'lgan edi."""
        problems = []
        for path, tree in self.modules():
            top = set()
            for node in tree.body:
                items = ast.walk(node) if isinstance(node, (ast.If, ast.Try)) else [node]
                for sub in items:
                    if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                        targets = (sub.targets if isinstance(sub, ast.Assign)
                                   else [sub.target])
                        top.update(t.id for t in targets if isinstance(t, ast.Name))
            for node in ast.walk(tree):
                if isinstance(node, ast.Global):
                    for name in node.names:
                        if name not in top:
                            problems.append(f"{path.name}: global {name}")
        self.assertEqual(problems, [], "global nomi o'z modulida e'lon qilinmagan")

    def test_no_import_cycles(self):
        """Modullar faqat yuqoridan pastga bog'lanadi."""
        edges = {}
        for path, tree in self.modules():
            deps = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                    deps.add(node.module)
            edges[path.stem] = deps
        state = {}

        def visit(mod, chain):
            if state.get(mod) == "done":
                return
            if state.get(mod) == "open":
                self.fail("halqa: " + " -> ".join(chain + [mod]))
            state[mod] = "open"
            for dep in sorted(edges.get(mod, ())):
                visit(dep, chain + [mod])
            state[mod] = "done"

        for mod in edges:
            visit(mod, [])

    def test_entry_point_stays_put(self):
        """Flutter ilovasi aynan shu faylni ishga tushiradi."""
        entry = self.PKG.parent / "desktop_processor.py"
        self.assertTrue(entry.is_file())
        self.assertIn("from subtitr.cli import main", entry.read_text(encoding="utf-8"))

    def test_root_points_at_the_app_folder_not_the_package(self):
        """`ROOT` — tools/, fonts/, .venv turgan papka; paket emas."""
        self.assertEqual(dp.ROOT, self.PKG.parent)


class TitleTests(unittest.TestCase):
    def test_underscores_become_spaces(self):
        self.assertEqual(dp.reading_title("Моё_видео"), "Моё видео")

    def test_quality_suffix_is_stripped(self):
        self.assertEqual(dp.reading_title("Клуб_страхаs1s1q480"), "Клуб страха")

    def test_empty_falls_back(self):
        self.assertEqual(dp.reading_title(""), "Matn")


class RequirementsTests(unittest.TestCase):
    """O'rnatiladigan paketlar ro'yxati bitta manbadan kelishi kerak.

    Ilgari ro'yxat `install_deps()` ichida qo'lda takrorlangan edi va
    `faster-whisper` o'sha nusxadan tushib qolgandi. U bilan birga Groq
    yo'lidagi VAD ham (`faster_whisper.vad`) jimgina ishlamay qolardi."""

    def test_requirements_file_is_the_source(self):
        packages = m_pipe.required_packages()
        from_file = [
            line.split(" #", 1)[0].strip()
            for line in dp.core.REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(packages, from_file)

    def test_faster_whisper_is_installed_by_the_button(self):
        self.assertTrue(
            any("faster-whisper" in pkg for pkg in m_pipe.required_packages()),
            "faster-whisper ro'yxatda yo'q — VAD va lokal transkripsiya o'chadi",
        )

    def test_fallback_covers_every_requirement(self):
        """Fayl topilmasa ham zaxira ro'yxat to'liq bo'lsin."""
        def name(spec: str) -> str:
            return spec.split(">=")[0].split("==")[0].strip()

        fallback = {name(p) for p in m_pipe.FALLBACK_PACKAGES}
        for spec in m_pipe.required_packages():
            self.assertIn(name(spec), fallback)


class DownloadCacheTests(unittest.TestCase):
    """Bitta video ikki marta yuklanmasin, kesh esa cheksiz o'smasin."""

    def test_youtube_variants_share_one_key(self):
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&si=abc",
            "https://youtu.be/dQw4w9WgXcQ?t=0",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ&feature=share",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        ]
        keys = {m_media.download_cache_key(u) for u in urls}
        self.assertEqual(len(keys), 1, f"bir xil video uchun {len(keys)} ta kalit")

    def test_different_videos_keep_different_keys(self):
        self.assertNotEqual(
            m_media.download_cache_key("https://youtu.be/aaaaaaaaaaa"),
            m_media.download_cache_key("https://youtu.be/bbbbbbbbbbb"),
        )

    def test_case_sensitive_ids_survive_on_other_sites(self):
        """Ko'p saytlarda ID registrga sezgir — pastki registrga tushirilmasin."""
        self.assertNotEqual(
            m_media.download_cache_key("https://example.com/v/AbC"),
            m_media.download_cache_key("https://example.com/v/abc"),
        )

    def test_prune_removes_oldest_and_spares_the_new_file(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for i, nom in enumerate(["eski.mp4", "orta.mp4", "yangi.mp4"]):
                f = d / nom
                f.write_bytes(b"x" * 200)
                os.utime(f, (1000 + i * 100, 1000 + i * 100))
            (d / "hujjat.txt").write_bytes(b"y" * 500)
            old_env = os.environ.get("SUBTITR_DL_CACHE_GB")
            # 3 x 200 bayt = 600; chegara 450 -> faqat eng eskisi o'chadi.
            os.environ["SUBTITR_DL_CACHE_GB"] = str(450 / 1024 ** 3)
            try:
                freed = m_media.prune_download_cache(d, keep=d / "yangi.mp4")
            finally:
                if old_env is None:
                    os.environ.pop("SUBTITR_DL_CACHE_GB", None)
                else:
                    os.environ["SUBTITR_DL_CACHE_GB"] = old_env
            left = {p.name for p in d.iterdir()}
            self.assertEqual(freed, 200)
            self.assertNotIn("eski.mp4", left)
            self.assertIn("yangi.mp4", left)
            self.assertIn("hujjat.txt", left, "video bo'lmagan fayl o'chirilmasin")

    def test_prune_disabled_by_zero_limit(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "a.mp4").write_bytes(b"x" * 1000)
            old_env = os.environ.get("SUBTITR_DL_CACHE_GB")
            os.environ["SUBTITR_DL_CACHE_GB"] = "0"
            try:
                self.assertEqual(m_media.prune_download_cache(d), 0)
            finally:
                if old_env is None:
                    os.environ.pop("SUBTITR_DL_CACHE_GB", None)
                else:
                    os.environ["SUBTITR_DL_CACHE_GB"] = old_env
            self.assertTrue((d / "a.mp4").exists())


class SubtitleFileTests(unittest.TestCase):
    """SRT/VTT o'qish-yozishdagi tuzatishlar."""

    def test_vtt_leaves_no_temp_file(self):
        """Ilgari har VTT uchun TMP_DIR ga `.srt` yozilar va qolib ketardi."""
        dp.core.TMP_DIR.mkdir(parents=True, exist_ok=True)
        before = set(dp.core.TMP_DIR.rglob("*"))
        with tempfile.TemporaryDirectory() as tmp:
            vtt = Path(tmp) / "kino.vtt"
            vtt.write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nSalom, Mr. Smith.\n",
                encoding="utf-8",
            )
            segments = m_media.parse_vtt(vtt)
        self.assertEqual(set(dp.core.TMP_DIR.rglob("*")), before)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Salom, Mr. Smith.")
        self.assertAlmostEqual(segments[0].end, 3.5)

    def test_srt_never_writes_three_lines(self):
        """SRT me'yori — 2 qator; `wrap_text` uchtagacha chiqarardi."""
        long_text = (
            "Bu juda uzun tarjima qatori bo'lib, u albatta bir nechta qatorga "
            "bo'linishi kerak va hech qanday so'z yo'qolmasligi shart"
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a.srt"
            m_media.write_srt(out, [seg(0.0, 4.0, long_text)])
            body = out.read_text(encoding="utf-8-sig").strip().splitlines()
        text_lines = body[2:]
        self.assertEqual(len(text_lines), 2)
        self.assertEqual(" ".join(" ".join(text_lines).split()), long_text)


class ModelDefaultTests(unittest.TestCase):
    """Kod ichidagi standart modellar `.env.example` bilan mos kelsin.

    Mos kelmasa foydalanuvchi namunani o'qib bir modelni kutadi-yu,
    boshqasini (ba'zan ancha qimmatini) oladi."""

    ENV_TO_CODE = {
        "GEMINI_MODEL": "gemini",
        "OPENAI_MODEL": "openai",
        "ANTHROPIC_MODEL": "anthropic",
        "GROQ_TEXT_MODEL": "groq",
    }

    def _env_example(self) -> dict[str, str]:
        raw = (Path(__file__).resolve().parent.parent / ".env.example").read_text(
            encoding="utf-8"
        )
        return {
            k.strip(): v.strip()
            for k, _, v in (line.partition("=") for line in raw.splitlines())
            if k.strip() and not k.strip().startswith("#")
        }

    def test_defaults_match_env_example(self):
        import re

        src = (Path(__file__).resolve().parent.parent / "subtitr" / "translate.py").read_text(
            encoding="utf-8"
        )
        env = self._env_example()
        for var in self.ENV_TO_CODE:
            match = re.search(rf'"{var}",\s*\n\s*"([^"]+)"', src)
            self.assertIsNotNone(match, f"{var} uchun standart topilmadi")
            self.assertEqual(
                match.group(1), env[var],
                f"{var}: kodda {match.group(1)!r}, .env.example da {env[var]!r}",
            )


class ImmutabilityTests(unittest.TestCase):
    """Bo'lak (Segment) kesh va sessiya fayli orqali o'tadi — uni joyida
    o'zgartirish kim qachon o'zgartirganini kuzatishni imkonsiz qiladi."""

    def test_segment_cannot_be_mutated(self):
        import dataclasses

        item = seg(0.0, 1.0, "salom")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.end = 5.0  # type: ignore[misc]

    def test_word_cannot_be_mutated(self):
        import dataclasses

        word = dp.Word(0.0, 1.0, "salom")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            word.word = "boshqa"  # type: ignore[misc]

    def test_frozen_segments_are_hashable(self):
        """Muzlatish bonusi: endi to'plam/lug'at kaliti bo'la oladi."""
        self.assertEqual(len({seg(0.0, 1.0, "a"), seg(0.0, 1.0, "a")}), 1)

    def test_overlap_trimming_still_works(self):
        """`frozen` dan keyin ustma-ust bo'laklar baribir kesilishi kerak."""
        a, b = seg(0.0, 5.0, "birinchi"), seg(3.0, 6.0, "ikkinchi")
        merged = sorted([a, b], key=lambda x: x.start)
        trimmed = []
        for i, cur in enumerate(merged):
            if i + 1 < len(merged) and cur.end > merged[i + 1].start:
                cur = dp.Segment(cur.start, max(cur.start + 0.2, merged[i + 1].start), cur.text)
            trimmed.append(cur)
        self.assertEqual(trimmed[0].end, 3.0)
        self.assertEqual(trimmed[0].text, "birinchi")
        self.assertEqual(trimmed[1].start, 3.0)


class SessionVersionTests(unittest.TestCase):
    """Eski sessiya fayli jimgina yarim ishlamasligi kerak."""

    def test_old_session_is_rejected_with_a_clear_message(self):
        import json

        from subtitr.pipeline import SESSION_VERSION, render_session

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps({
                "segments": [{"start": 0, "end": 1, "original": "a", "translated": "b"}],
                "video": "/yoq", "mode": "srt",
            }), encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                render_session(str(path))
        message = str(ctx.exception)
        self.assertIn("eski", message)
        self.assertIn(str(SESSION_VERSION), message)
        # Foydalanuvchiga nima qilish kerakligi va pul ketmasligi aytilsin.
        self.assertIn("qaytadan tayyorlang", message)


class DiskSpaceTests(unittest.TestCase):
    """Joy tugaganda ffmpeg tushunarsiz xato beradi — oldindan aytamiz."""

    def test_enough_space_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "kino.mp4"
            video.write_bytes(b"x" * 1024)
            dp.core.require_disk_space(video, Path(tmp))  # xato bo'lmasligi kerak

    def test_not_enough_space_explains_how_much(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "kino.mp4"
            video.write_bytes(b"x" * 1024)
            with self.assertRaises(RuntimeError) as ctx:
                dp.core.require_disk_space(video, Path(tmp), factor=10 ** 12)
        message = str(ctx.exception)
        self.assertIn("GB bo'sh", message)
        self.assertIn("GB kerak", message)

    def test_unmeasurable_path_does_not_block_the_job(self):
        """O'lchab bo'lmasa ish to'xtamasin — bu faqat ogohlantirish."""
        dp.core.require_disk_space(Path("/yoq/bunday/fayl.mp4"), Path("/yoq/bunday"))


class LoggingTests(unittest.TestCase):
    """Log — xatoni topishning yagona yo'li, lekin kalit sizdirmasligi shart."""

    def test_api_keys_are_redacted(self):
        samples = {
            "gsk_aBcDeFgH1234567890xyzQ": "Groq",
            "sk-ant-api03-AbCdEf1234567890": "Claude",
            "sk-proj-AbCdEf1234567890xyz": "OpenAI",
            "AIzaSyAbCdEf1234567890xyz": "Gemini (eski format)",
            "AQ.Ab8RN6JxyzAbCdEfGh": "Gemini (yangi format)",
        }
        for secret, label in samples.items():
            masked = dp.core.redact(f"xato: invalid key {secret} provided")
            self.assertNotIn(secret, masked, f"{label} kaliti logga tushib ketdi")

    def test_plain_text_is_untouched(self):
        message = "ffmpeg topilmadi. Uni dastur papkasiga qo'shing."
        self.assertEqual(dp.core.redact(message), message)

    def test_importing_the_package_writes_no_log_file(self):
        """Faqat import qilish (test, kutubxona) disk fayl yaratmasin."""
        self.assertTrue(
            all(isinstance(h, __import__("logging").NullHandler)
                for h in dp.core.log.handlers),
            "setup_logging() chaqirilmagan holda ham handler ulangan",
        )

    def test_emit_mirrors_messages_into_the_log(self):
        import io
        import logging

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        dp.core.log.addHandler(handler)
        dp.core.log.setLevel(logging.INFO)
        try:
            dp.emit("progress", message="Tarjima 10/38", progress=0.42)
            dp.emit("error", message="kalit yaroqsiz gsk_aBcDeFgH1234567890xyz")
        finally:
            dp.core.log.removeHandler(handler)
            dp.core.log.setLevel(logging.NOTSET)
        written = stream.getvalue()
        self.assertIn("Tarjima 10/38", written)
        self.assertIn("42%", written)
        self.assertNotIn("gsk_aBcDeFgH1234567890xyz", written)

    def test_log_dir_follows_the_data_dir(self):
        """LOG_DIR boshqa ishchi papkalar bilan bir joyda bo'lsin."""
        self.assertEqual(dp.core.LOG_DIR.parent, dp.core.CACHE_DIR.parent)
        self.assertEqual(dp.core.LOG_DIR.name, "logs")


class ParallelTranslationTests(unittest.TestCase):
    """Tarjima to'plamlari parallel yuboriladi.

    Eng katta xavf: to'plamlar BOSHQA TARTIBDA tugaydi va natijalar
    aralashib ketadi — ekranda boshqa gapning tarjimasi chiqadi. Shu
    sababli tartib har testda tekshiriladi."""

    def setUp(self):
        self._real = m_tx.ai_translate_batch
        self.seen: list[list[str]] = []
        self.lock = __import__("threading").Lock()

    def tearDown(self):
        m_tx.ai_translate_batch = self._real

    def _segments(self, n: int) -> list:
        return [seg(float(i), float(i) + 1.0, f"line {i}") for i in range(n)]

    def _stub(self, delay_for=None):
        """`delay_for(texts) -> soniya` bilan tugash tartibini boshqaramiz."""
        import time

        def fake(texts, target_lang, source_lang="", before=None, after=None, glossary=None):
            with self.lock:
                self.seen.append(list(texts))
            if delay_for is not None:
                time.sleep(delay_for(texts))
            return [t.replace("line", "qator") for t in texts], "claude"

        m_tx.ai_translate_batch = fake

    def test_order_is_preserved_when_batches_finish_out_of_order(self):
        import os

        # Birinchi to'plam ENG SEKIN tugaydi — natija oxirida keladi.
        def delay(texts):
            return 0.25 if texts[0] == "line 0" else 0.01

        self._stub(delay)
        old = os.environ.get("TRANSLATE_BATCH"), os.environ.get("TRANSLATE_WORKERS")
        os.environ["TRANSLATE_BATCH"] = "10"
        os.environ["TRANSLATE_WORKERS"] = "4"
        try:
            out, provider = m_tx.translate_segments(self._segments(40), "uz", "en")
        finally:
            for k, v in zip(("TRANSLATE_BATCH", "TRANSLATE_WORKERS"), old):
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

        self.assertEqual(len(out), 40)
        self.assertEqual(provider, "claude")
        for i, item in enumerate(out):
            self.assertEqual(item.text, f"qator {i}", f"{i}-qator tarjimasi aralashdi")
            # Vaqtlar asl bo'lakdan olinishi kerak.
            self.assertEqual(item.start, float(i))

    def test_batches_actually_run_in_parallel(self):
        import os
        import time

        self._stub(lambda texts: 0.15)
        old = os.environ.get("TRANSLATE_BATCH"), os.environ.get("TRANSLATE_WORKERS")
        os.environ["TRANSLATE_BATCH"] = "10"
        try:
            os.environ["TRANSLATE_WORKERS"] = "1"
            t0 = time.monotonic()
            m_tx.translate_segments(self._segments(40), "uz", "en")
            sequential = time.monotonic() - t0

            os.environ["TRANSLATE_WORKERS"] = "4"
            t0 = time.monotonic()
            m_tx.translate_segments(self._segments(40), "uz", "en")
            parallel = time.monotonic() - t0
        finally:
            for k, v in zip(("TRANSLATE_BATCH", "TRANSLATE_WORKERS"), old):
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

        # 4 ta to'plam x 0.15s: ketma-ket ~0.6s, 4 oqimda ~0.15s.
        self.assertLess(parallel, sequential * 0.6,
                        f"parallel {parallel:.2f}s vs ketma-ket {sequential:.2f}s")

    def test_cached_lines_are_not_sent_to_the_ai(self):
        import json
        import os

        self._stub()
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "tr.json"
            segments = self._segments(20)
            # Birinchi 10 qator allaqachon tarjima qilingan.
            cache.write_text(json.dumps({
                m_tx._text_key(x.text): f"keshdan {i}"
                for i, x in enumerate(segments[:10])
            }), encoding="utf-8")
            old = os.environ.get("TRANSLATE_BATCH")
            os.environ["TRANSLATE_BATCH"] = "10"
            try:
                out, _ = m_tx.translate_segments(
                    segments, "uz", "en", cache_path=cache
                )
            finally:
                os.environ.pop("TRANSLATE_BATCH", None) if old is None \
                    else os.environ.__setitem__("TRANSLATE_BATCH", old)

        self.assertEqual(len(self.seen), 1, "keshdagi to'plam ham AI'ga yuborildi")
        self.assertEqual(out[0].text, "keshdan 0")
        self.assertEqual(out[10].text, "qator 10")

    def test_single_worker_matches_parallel_result(self):
        """TRANSLATE_WORKERS=1 (eski xatti-harakat) bir xil natija bersin."""
        import os

        results = {}
        old = os.environ.get("TRANSLATE_BATCH"), os.environ.get("TRANSLATE_WORKERS")
        os.environ["TRANSLATE_BATCH"] = "7"
        try:
            for workers in ("1", "4"):
                os.environ["TRANSLATE_WORKERS"] = workers
                self.seen = []
                self._stub()
                out, _ = m_tx.translate_segments(self._segments(30), "uz", "en")
                results[workers] = [x.text for x in out]
        finally:
            for k, v in zip(("TRANSLATE_BATCH", "TRANSLATE_WORKERS"), old):
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.assertEqual(results["1"], results["4"])


class VocabContextTests(unittest.TestCase):
    """Lug'at tarjimasiga so'z uchragan GAP ham yuboriladi.

    Kontekstsiz ko'p ma'noli so'z tasodifiy ma'noda tarjima bo'ladi.
    Haqiqiy Groq bilan o'lchangan (5 so'zdan 3 tasi to'g'rilandi):
      bank  -> "bank"      => "qirg'oq"   (daryo qirg'og'i)
      right -> "to'g'ri"   => "o'ng"      (yo'nalish)
      light -> "yorug'lik" => "yengil"    (vazn)
    """

    def test_sentence_is_found_by_word_timestamp(self):
        segments = [
            seg(0.0, 3.0, "Biz daryo qirg'og'ida o'tirdik."),
            seg(3.0, 6.0, "Chiroq yonida o'ngga buriling."),
            seg(6.0, 9.0, "Qutini ko'tarish oson edi."),
        ]
        starts = [x.start for x in segments]
        for when, expected in ((1.0, 0), (4.5, 1), (7.0, 2)):
            found = m_vocab.sentence_for(dp.Word(when, when + 0.3, "x"), segments, starts)
            self.assertEqual(found, segments[expected].text, f"{when}s")

    def test_word_on_a_boundary_still_gets_a_sentence(self):
        segments = [seg(0.0, 3.0, "birinchi"), seg(3.0, 6.0, "ikkinchi")]
        starts = [x.start for x in segments]
        found = m_vocab.sentence_for(dp.Word(3.0, 3.4, "x"), segments, starts)
        self.assertIn(found, {"birinchi", "ikkinchi"})

    def test_no_segments_means_no_context(self):
        self.assertEqual(m_vocab.sentence_for(dp.Word(1.0, 2.0, "x"), [], []), "")

    def test_build_vocabulary_passes_the_sentence_along(self):
        captured = {}

        def fake(words, target_lang, contexts=None, source_lang="en"):
            captured["words"] = list(words)
            captured["contexts"] = list(contexts) if contexts else None
            return (["tarjima"] * len(words), [""] * len(words),
                    [""] * len(words), "claude")

        real = m_vocab.translate_word_list
        m_vocab.translate_word_list = fake
        try:
            m_vocab.build_vocabulary(
                [dp.Word(1.0, 1.5, "qirgoq")],
                "en", "uz",
                segments=[seg(0.0, 3.0, "Biz daryo qirg'og'ida o'tirdik.")],
            )
        finally:
            m_vocab.translate_word_list = real
        self.assertEqual(captured["words"], ["qirgoq"])
        self.assertEqual(captured["contexts"], ["Biz daryo qirg'og'ida o'tirdik."])

    def test_without_segments_context_is_omitted(self):
        """Eski chaqiruvlar (segmentsiz) ishlashda davom etsin."""
        captured = {}

        def fake(words, target_lang, contexts=None, source_lang="en"):
            captured["contexts"] = contexts
            return (["t"] * len(words), [""] * len(words),
                    [""] * len(words), "claude")

        real = m_vocab.translate_word_list
        m_vocab.translate_word_list = fake
        try:
            m_vocab.build_vocabulary([dp.Word(1.0, 1.5, "soz")], "en", "uz")
        finally:
            m_vocab.translate_word_list = real
        self.assertIsNone(captured["contexts"])

    def test_payload_carries_ctx_only_when_given(self):
        import os

        seen = []

        def capture(_prompt, payload):
            seen.append(payload)
            raise RuntimeError("to'xtatamiz — faqat payload kerak")

        env = {k: os.environ.get(k) for k in ("GROQ_API_KEY", "AI_MAX_ATTEMPTS")}
        os.environ["GROQ_API_KEY"] = "test"
        os.environ["AI_MAX_ATTEMPTS"] = "1"
        real_groq, real_backoff = m_tx.translate_groq, m_tx.ai_retry_backoff
        m_tx.translate_groq = capture
        m_tx.ai_retry_backoff = lambda attempt=0: None
        dp.core.AI_DISABLED.clear()
        try:
            m_tx.translate_word_list(["bank"], "uz")
            m_tx.translate_word_list(["bank"], "uz", contexts=["We sat on the river bank."])
        finally:
            m_tx.translate_groq, m_tx.ai_retry_backoff = real_groq, real_backoff
            dp.core.AI_DISABLED.clear()
            for k, v in env.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

        self.assertNotIn('"ctx"', seen[0], "kontekst berilmaganda ham yuborildi")
        self.assertIn('"ctx"', seen[-1], "kontekst berilgan, lekin yuborilmadi")
        self.assertIn("river bank", seen[-1])

    def test_long_context_is_trimmed(self):
        import os

        seen = []

        def capture(_prompt, payload):
            seen.append(payload)
            raise RuntimeError("to'xtatamiz")

        env = {k: os.environ.get(k) for k in ("GROQ_API_KEY", "AI_MAX_ATTEMPTS")}
        os.environ["GROQ_API_KEY"] = "test"
        os.environ["AI_MAX_ATTEMPTS"] = "1"
        real_groq, real_backoff = m_tx.translate_groq, m_tx.ai_retry_backoff
        m_tx.translate_groq = capture
        m_tx.ai_retry_backoff = lambda attempt=0: None
        dp.core.AI_DISABLED.clear()
        try:
            m_tx.translate_word_list(["soz"], "uz", contexts=["juda uzun gap " * 50])
        finally:
            m_tx.translate_groq, m_tx.ai_retry_backoff = real_groq, real_backoff
            dp.core.AI_DISABLED.clear()
            for k, v in env.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        ctx = __import__("json").loads(seen[0])["0"]["ctx"]
        self.assertLessEqual(len(ctx), m_tx.VOCAB_CONTEXT_CHARS)

    def test_vocab_cache_version_was_bumped(self):
        """Versiya oshirilmasa eski (kontekstsiz) lug'at keshdan qaytaverardi."""
        source = (Path(__file__).resolve().parent.parent / "subtitr" / "pipeline.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("vocab_v3_", source)
        self.assertNotIn("vocab_v2_", source)


class OfflineDictionaryTests(unittest.TestCase):
    """Kalitsiz rejimdagi zaxira lug'at.

    Ilgari u bitta tekis to'plam edi: 98 so'z, faqat ingliz->o'zbek.
    Rus tilidagi kontent (asosiy foydalanish) uchun hech narsa yo'q edi,
    ustiga NISHON til hisobga olinmas — rus tiliga tarjima so'ralganda
    ham o'zbekcha qaytarardi."""

    def test_russian_words_translate(self):
        for word, expected in (("привет", "salom"), ("спасибо", "rahmat"),
                               ("вчера", "kecha"), ("дети", "bolalar")):
            self.assertEqual(m_tx.offline_translate_word(word, "ru", "uz"), expected)

    def test_russian_phrases_translate(self):
        for text, expected in (("Не знаю", "bilmayman"),
                               ("Доброе утро", "xayrli tong"),
                               ("Как дела?", "qalaysiz?")):
            self.assertEqual(m_tx.offline_translate_text(text, "ru", "uz"), expected)

    def test_english_pair_still_works(self):
        self.assertEqual(m_tx.offline_translate_text("Thank you", "en", "uz"), "rahmat")
        self.assertEqual(m_tx.offline_translate_word("hello", "en", "uz"), "salom")

    def test_target_language_is_respected(self):
        """Ilgari rus tiliga so'ralganda ham o'zbekcha qaytarardi."""
        self.assertEqual(m_tx.offline_translate_text("hello", "en", "ru"), "")
        self.assertEqual(m_tx.offline_translate_word("hello", "en", "ru"), "hello")

    def test_unknown_pair_returns_nothing(self):
        self.assertEqual(m_tx.offline_translate_text("hallo", "de", "uz"), "")
        self.assertEqual(m_tx.offline_translate_word("hallo", "de", "uz"), "hallo")

    def test_capitalisation_is_preserved(self):
        self.assertEqual(m_tx.offline_translate_text("Привет", "ru", "uz"), "Salom")

    def test_no_duplicate_keys_in_any_dictionary(self):
        """Dict literal takroriy kalitni JIMGINA yutadi — ikkinchisi g'olib
        chiqadi va birinchi tarjima yo'qoladi. Shuning uchun manba kod
        AST darajasida tekshiriladi."""
        import ast
        import collections

        tree = ast.parse(
            (Path(__file__).resolve().parent.parent / "subtitr" / "core.py")
            .read_text(encoding="utf-8")
        )
        checked = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                name = getattr(node.target, "id", "")
            elif isinstance(node, ast.Assign):
                name = getattr(node.targets[0], "id", "")
            else:
                continue
            if name not in ("OFFLINE_WORDS", "OFFLINE_PHRASES"):
                continue
            for pair_key, inner in zip(node.value.keys, node.value.values):
                langs = tuple(e.value for e in pair_key.elts)
                keys = [k.value for k in inner.keys]
                dupes = [k for k, c in collections.Counter(keys).items() if c > 1]
                self.assertEqual(dupes, [], f"{name} {langs} da takroriy kalit")
                checked += 1
        self.assertGreaterEqual(checked, 4, "lug'atlar topilmadi")

    def test_every_dictionary_has_a_matching_phrase_table(self):
        """Har til juftligi uchun ikkala jadval ham bo'lsin."""
        self.assertEqual(
            set(dp.core.OFFLINE_WORDS), set(dp.core.OFFLINE_PHRASES)
        )

    def test_russian_dictionary_is_meaningfully_larger_than_before(self):
        self.assertGreaterEqual(len(dp.core.offline_words("ru", "uz")), 150)


class VocabCardTests(unittest.TestCase):
    """Ekrandagi lug'at kartochkalari ketma-ket suzib chiqadi.

    Kartochka davomiyligi minimal oraliqni ham belgilaydi (tezlik =
    masofa/vaqt). 4.0 soniyada sekundda ~3.2 kartochka sig'adi, shundan
    tez nutqda so'zlar tashlanadi. O'lchangan: haqiqiy 6 videoda (1980
    so'z) birorta ham tashlanmagan, lekin 4 so'z/sek dan boshlab
    mexanizm ishlaydi (80 so'zdan 8 ta, 5 so'z/sek da 20 ta)."""

    def _cards(self, path: Path) -> int:
        return sum(1 for ln in path.read_text(encoding="utf-8").splitlines()
                   if ",Vocab," in ln)

    def _write(self, tmp: Path, rate: float, count: int, duration: str | None):
        import os

        words = [dp.Word(i / rate, i / rate + 0.15, f"word{i}") for i in range(count)]
        vocab_map = {f"word{i}": f"soz{i}" for i in range(count)}
        old = os.environ.get("SUBTITR_VOCAB_DURATION")
        if duration is None:
            os.environ.pop("SUBTITR_VOCAB_DURATION", None)
        else:
            os.environ["SUBTITR_VOCAB_DURATION"] = duration
        out = tmp / f"a_{rate}_{duration}.ass"
        try:
            m_sub.write_ass(
                out, [seg(0.0, count / rate + 5, "matn")], None,
                words, vocab_map, 1920, 1080,
            )
        finally:
            os.environ.pop("SUBTITR_VOCAB_DURATION", None) if old is None \
                else os.environ.__setitem__("SUBTITR_VOCAB_DURATION", old)
        return self._cards(out)

    def test_normal_speech_loses_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._write(Path(tmp), 2.0, 40, None), 40)

    def test_dense_speech_drops_cards_with_the_default_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            shown = self._write(Path(tmp), 5.0, 60, "4.0")
        self.assertLess(shown, 60, "zich nutqda ham hammasi sig'di?")

    def test_shorter_duration_fits_more_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            at_four = self._write(Path(tmp), 5.0, 60, "4.0")
            at_three = self._write(Path(tmp), 5.0, 60, "3.0")
        self.assertGreater(at_three, at_four)
        self.assertEqual(at_three, 60)

    def test_dropped_cards_are_reported(self):
        """Ilgari so'zlar jimgina tashlanardi — foydalanuvchi sababini bilmasdi."""
        import contextlib
        import io

        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(buffer):
                self._write(Path(tmp), 5.0, 60, "4.0")
        self.assertIn("kartochkasi sig'madi", buffer.getvalue())
        self.assertIn("SUBTITR_VOCAB_DURATION", buffer.getvalue())

    def test_nothing_is_reported_when_all_cards_fit(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(buffer):
                self._write(Path(tmp), 2.0, 40, None)
        self.assertNotIn("sig'madi", buffer.getvalue())


class ReadingSpeedTests(unittest.TestCase):
    """Subtitr vaqtlari: ustma-ustlik bo'lmasin, tanaffus bo'lsin, lekin
    matnni o'qib bo'lish imkoniyati yo'qolmasin.

    Haqiqiy ma'lumotda (350 bo'lak) o'lchangan:
      ustma-ustlik 0 -> 0,  o'qish buzilgan 7 -> 7,  tanaffus 3 -> 153
    Ustma-ust SRT da: 1 -> 0.
    """

    def _overlaps(self, out):
        return sum(1 for a, b in zip(out, out[1:]) if a.end > b.start)

    def test_overlapping_input_is_fixed(self):
        """Foydalanuvchi qo'ygan `.srt` (fansub) ustma-ust qatorlarga to'la."""
        segments = [
            seg(1.0, 6.0, "Birinchi personaj uzoq gapiradi"),
            seg(3.0, 8.0, "Ikkinchi personaj ham gapiradi"),
        ]
        out = m_clean.enforce_reading_speed(segments)
        self.assertEqual(self._overlaps(out), 0)
        self.assertLessEqual(out[0].end, out[1].start)

    def test_back_to_back_subtitles_get_a_gap(self):
        """`gap` o'zgaruvchisi kodda bor edi, lekin hech qachon qo'llanmagan."""
        segments = [seg(0.0, 5.0, "Birinchi qator"), seg(5.0, 10.0, "Ikkinchi qator")]
        out = m_clean.enforce_reading_speed(segments)
        self.assertGreater(out[1].start - out[0].end, 0.0, "tanaffus yo'q")
        self.assertAlmostEqual(out[0].end, 5.0 - 0.08, places=6)

    def test_shortening_never_breaks_the_reading_speed(self):
        """Tanaffus me'yori uchun matnni o'qib bo'lmaydigan qilib qo'ymaymiz."""
        # 100 belgi, 20 belgi/sek => kamida 5 soniya kerak.
        text = "x" * 100
        segments = [seg(0.0, 5.0, text), seg(5.0, 9.0, "keyingi")]
        out = m_clean.enforce_reading_speed(segments)
        duration = out[0].end - out[0].start
        self.assertGreaterEqual(
            duration, 100 / 20.0 - 1e-6,
            "qisqartirish o'qish vaqtidan past tushdi",
        )
        self.assertEqual(self._overlaps(out), 0)

    def test_near_simultaneous_pair_is_not_reduced_to_a_flash(self):
        """0.02 soniyalik chaqnash ustma-ust turgandan ham yomon."""
        segments = [seg(1.0, 6.0, "uzun qator"), seg(1.1, 5.0, "deyarli bir vaqtda")]
        out = m_clean.enforce_reading_speed(segments)
        self.assertGreaterEqual(out[0].end - out[0].start, 0.3)

    def test_short_segment_is_extended_but_not_into_the_next(self):
        segments = [seg(0.0, 0.2, "qisqa"), seg(0.5, 4.0, "keyingi")]
        out = m_clean.enforce_reading_speed(segments)
        self.assertGreater(out[0].end, 0.2, "minimal vaqtga cho'zilmadi")
        self.assertEqual(self._overlaps(out), 0)

    def test_gap_is_configurable(self):
        import os

        segments = [seg(0.0, 5.0, "bir"), seg(5.0, 10.0, "ikki")]
        old = os.environ.get("SUB_MIN_GAP")
        os.environ["SUB_MIN_GAP"] = "0.25"
        try:
            out = m_clean.enforce_reading_speed(segments)
        finally:
            os.environ.pop("SUB_MIN_GAP", None) if old is None \
                else os.environ.__setitem__("SUB_MIN_GAP", old)
        self.assertAlmostEqual(out[0].end, 4.75, places=6)

    def test_last_segment_is_not_shortened(self):
        segments = [seg(0.0, 3.0, "oxirgi qator")]
        out = m_clean.enforce_reading_speed(segments)
        self.assertGreaterEqual(out[0].end, 3.0)

    def test_empty_input(self):
        self.assertEqual(m_clean.enforce_reading_speed([]), [])


class GlossaryTests(unittest.TestCase):
    """Glossariy film bo'ylab ISM izchilligini ta'minlashi kerak.

    Haqiqiy rus matnida (60 bo'lak) o'lchangan:
      oldin:  Вася, Бабушka, Иван   ("Бабушка" -> "buva" — xato tarjima,
                                     ustiga u ism ham emas)
      hozir:  Вася, Иван / Ивану    (kelishik shakllari birlashtirilgan)
    """

    def setUp(self):
        import os

        self._env = {k: os.environ.get(k) for k in ("GROQ_API_KEY",)}
        os.environ["GROQ_API_KEY"] = "test-key"
        self._real = m_tx.translate_word_list

    def tearDown(self):
        import os

        m_tx.translate_word_list = self._real
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def test_sentence_initial_words_are_not_names(self):
        """Gap boshidagi har qanday so'z bosh harfli — bu ism degani emas."""
        segments = [
            seg(0.0, 2.0, "Но Вася ushlab oldi."),
            seg(2.0, 4.0, "Он Vasyani ko'rdi."),
            seg(4.0, 6.0, "Мальчик Вася keldi."),
        ]
        freq, proper = m_tx.name_frequencies(segments)
        self.assertIn("Вася", proper)
        for word in ("Но", "Он", "Мальчик"):
            self.assertNotIn(word, proper, f"{word} ism deb hisoblandi")
            self.assertIn(word, freq, "chastota baribir sanalishi kerak")

    def test_case_forms_share_one_target(self):
        """Rus ismi kelishikda o'zgaradi — hammasi bitta tarjimaga ketsin."""
        def fake(words, target_lang, contexts=None, source_lang="en"):
            # Model lemmani qaytaradi; shu bilan shakllar guruhlanadi.
            lemmas = ["иван" if w.startswith("Иван") else w.lower() for w in words]
            return (["Ivan" if w.startswith("Иван") else "X" for w in words],
                    ["noun"] * len(words), lemmas, "claude")

        m_tx.translate_word_list = fake
        segments = [
            seg(0.0, 2.0, "Men Иван bilan keldim."),
            seg(2.0, 4.0, "Kitobni Ивану berdim."),
            seg(4.0, 6.0, "U Ивана ko'rdi."),
        ]
        glossary = m_tx.build_glossary(segments, "uz", "ru")
        self.assertEqual(
            {k: v for k, v in glossary.items() if k.startswith("Иван")},
            {"Иван": "Ivan", "Ивану": "Ivan", "Ивана": "Ivan"},
        )

    def test_rare_case_forms_are_kept(self):
        """"Иван" 5 marta, "Ивану" 1 marta — ikkinchisi tushib qolmasin."""
        def fake(words, target_lang, contexts=None, source_lang="en"):
            return (["Ivan"] * len(words), ["noun"] * len(words),
                    ["иван"] * len(words), "claude")

        m_tx.translate_word_list = fake
        segments = [seg(float(i), i + 1.0, "Men Иван bilan keldim.") for i in range(5)]
        segments.append(seg(10.0, 11.0, "Kitobni Ивану berdim."))
        glossary = m_tx.build_glossary(segments, "uz", "ru")
        self.assertIn("Ивану", glossary)

    def test_pronouns_and_verbs_are_excluded(self):
        """Olmosh/fe'lni "doim shunday tarjima qil" deb majburlash zarar."""
        def fake(words, target_lang, contexts=None, source_lang="en"):
            pos = {"Он": "pronoun", "Купила": "verb", "Красивый": "adjective",
                   "Вася": "noun"}
            return (["X"] * len(words), [pos.get(w, "noun") for w in words],
                    [w.lower() for w in words], "claude")

        m_tx.translate_word_list = fake
        segments = [
            seg(float(i), i + 1.0, f"Men {w} bilan keldim.")
            for i in range(3) for w in ("Он",)
        ] + [
            seg(10.0 + i, 11.0 + i, f"Men {w} bilan keldim.")
            for i, w in enumerate(["Купила"] * 3)
        ] + [
            seg(20.0 + i, 21.0 + i, "Men Вася bilan keldim.") for i in range(3)
        ]
        glossary = m_tx.build_glossary(segments, "uz", "ru")
        self.assertIn("Вася", glossary)
        self.assertNotIn("Он", glossary)
        self.assertNotIn("Купила", glossary)

    def test_group_needs_three_mentions_in_total(self):
        def fake(words, target_lang, contexts=None, source_lang="en"):
            return (["X"] * len(words), ["noun"] * len(words),
                    [w.lower() for w in words], "claude")

        m_tx.translate_word_list = fake
        # Ikki marta — chegaradan past.
        segments = [seg(float(i), i + 1.0, "Men Петя bilan keldim.") for i in range(2)]
        self.assertEqual(m_tx.build_glossary(segments, "uz", "ru"), {})
        # Uchinchisi qo'shilsa tushadi.
        segments.append(seg(9.0, 10.0, "Men Петя bilan keldim."))
        self.assertIn("Петя", m_tx.build_glossary(segments, "uz", "ru"))

    def test_no_names_means_empty_glossary(self):
        segments = [seg(0.0, 2.0, "Но он keldi."), seg(2.0, 4.0, "Это yaxshi.")]
        self.assertEqual(m_tx.build_glossary(segments, "uz", "ru"), {})


class AllModeTests(unittest.TestCase):
    """"Hammasi" rejimi BITTA video berishi kerak.

    Render eng sekin bosqich va to'siq GPU kodlagichi, u ikki oqimni
    tezroq qila olmaydi (o'lchangan: 1 chiqish 6.1s, 2 chiqish 12.2s;
    bir o'tishda ikki chiqish 11.3s, parallel 10.7s — 7-12%). Shuning
    uchun yagona haqiqiy tejash — ortiqcha videoni render qilmaslik."""

    def test_all_renders_exactly_one_video(self):
        from subtitr.pipeline import VIDEO_MODES, modes_for

        videos = [m for m in modes_for("all") if m in VIDEO_MODES]
        self.assertEqual(videos, ["dual_vocab"])

    def test_all_still_produces_every_document(self):
        from subtitr.pipeline import modes_for

        produced = set(modes_for("all"))
        for kind in ("srt", "transcript", "reading", "vocabulary"):
            self.assertIn(kind, produced, f"{kind} 'Hammasi' dan tushib qoldi")

    def test_plain_modes_pass_through_unchanged(self):
        from subtitr.pipeline import modes_for

        for mode in ("dual_vocab", "original_vocab", "translated", "reading", "srt"):
            self.assertEqual(modes_for(mode), [mode])

    def test_ui_description_matches_one_video(self):
        """Interfeys "Video" deb BIRLIKDA yozadi — kod ham shunday bo'lsin."""
        home = (
            Path(__file__).resolve().parent.parent
            / "subtitr_app" / "lib" / "screens" / "home_screen.dart"
        ).read_text(encoding="utf-8")
        self.assertIn("'Video, SRT, matn va lug\\'at'", home)


class AudioPassthroughTests(unittest.TestCase):
    """Audio allaqachon MP4 ga mos bo'lsa qayta kodlanmasligi kerak.

    O'lchangan (10 daqiqalik klip, VAAPI video): qayta kodlash 40.1s,
    ko'chirish 15.1s. GPU video kodlaganda CPU'dagi AAC butun quvurni
    ushlab turadi, ustiga bir avlod sifat yo'qoladi."""

    def setUp(self):
        import os

        self._real = m_sub.probe_audio_codec
        self._env = os.environ.get("SUB_AUDIO")

    def tearDown(self):
        import os

        m_sub.probe_audio_codec = self._real
        os.environ.pop("SUB_AUDIO", None) if self._env is None \
            else os.environ.__setitem__("SUB_AUDIO", self._env)

    def _args_for(self, codec: str) -> list[str]:
        m_sub.probe_audio_codec = lambda _p: codec
        return m_sub.audio_args_for(Path("/yoq/kino.mp4"))

    def test_mp4_safe_codecs_are_copied(self):
        for codec in ("aac", "mp3", "ac3", "eac3", "alac"):
            self.assertEqual(self._args_for(codec), ["-c:a", "copy"], codec)

    def test_other_codecs_are_converted_to_aac(self):
        # YouTube sukut bo'yicha Opus beradi — u MP4 uchun o'girilishi kerak.
        for codec in ("opus", "vorbis", "flac", "pcm_s16le", ""):
            self.assertEqual(self._args_for(codec)[:2], ["-c:a", "aac"], codec)

    def test_env_override_forces_the_old_behaviour(self):
        import os

        os.environ["SUB_AUDIO"] = "aac"
        self.assertEqual(self._args_for("aac")[:2], ["-c:a", "aac"])
        os.environ["SUB_AUDIO"] = "copy"
        self.assertEqual(self._args_for("opus"), ["-c:a", "copy"])

    def test_download_format_prefers_m4a_over_opus(self):
        """Yuklashda m4a so'ralsa, keyin kuydirishda qayta kodlash kerak bo'lmaydi."""
        source = (Path(__file__).resolve().parent.parent / "subtitr" / "media.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("ba[ext=m4a]", source)
        # Zaxira zanjiri saqlanib qolsin — m4a topilmasa ham yuklanishi kerak.
        self.assertIn("/bv*+ba/b", source)


class GroqChunkTests(unittest.TestCase):
    """Uzun kino 20 daqiqalik bo'laklarga bo'linib Groq'ga yuboriladi.

    Bo'laklar parallel ketadi, lekin natija VAQT bo'yicha to'g'ri
    tartibda yig'ilishi shart — aks holda subtitr vaqtlari aralashib,
    ekranda keyingi sahnaning matni chiqadi."""

    def setUp(self):
        import os

        self._real_tx = m_tr._groq_transcribe_file
        self._real_run = m_tr.run
        self._real_dur = m_tr.probe_duration_seconds
        self._real_rescan = m_tr.rescan_swallowed_speech
        self._env = {
            k: os.environ.get(k)
            for k in ("GROQ_API_KEY", "GROQ_AUDIO_CHUNK_BYTES",
                      "GROQ_CHUNK_SECONDS", "GROQ_AUDIO_WORKERS")
        }
        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["GROQ_AUDIO_CHUNK_BYTES"] = "1"      # har doim bo'laklaymiz
        os.environ["GROQ_CHUNK_SECONDS"] = "60"
        # ffmpeg kesishini taqlid qilamiz: fayl yasaladi, qaytish kodi 0.
        self.cut: list[float] = []

        class FakeProc:
            returncode = 0
            stderr = ""

        def fake_run(cmd, cwd=None):
            out = Path(cmd[-1])
            out.write_bytes(b"audio")
            return FakeProc()

        m_tr.run = fake_run
        m_tr.probe_duration_seconds = lambda _p: 300.0   # 5 daqiqa -> 5 bo'lak
        m_tr.rescan_swallowed_speech = (
            lambda _t, _a, _l, segments, words, source_media=None: (segments, words)
        )

    def tearDown(self):
        import os

        m_tr._groq_transcribe_file = self._real_tx
        m_tr.run = self._real_run
        m_tr.probe_duration_seconds = self._real_dur
        m_tr.rescan_swallowed_speech = self._real_rescan
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def _stub(self, delay_for=None, fail_at=None):
        import time

        def fake(_client, _models, path, _language, offset):
            if delay_for is not None:
                time.sleep(delay_for(offset))
            if fail_at is not None and abs(offset - fail_at) < 0.01:
                raise RuntimeError("soxta xato")
            # Har bo'lak o'z siljishi bilan bitta bo'lak qaytaradi.
            return (
                [dp.Segment(offset + 1.0, offset + 2.0, f"qism {int(offset // 60)}")],
                [dp.Word(offset + 1.0, offset + 1.5, f"soz{int(offset // 60)}")],
                "english",
            )

        m_tr._groq_transcribe_file = fake

    def test_chunks_are_ordered_by_time_not_by_completion(self):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "audio.webm"
            audio.write_bytes(b"x" * 100)
            # BIRINCHI bo'lak eng sekin tugaydi.
            self._stub(delay_for=lambda off: 0.2 if off == 0.0 else 0.01)
            os.environ["GROQ_AUDIO_WORKERS"] = "5"
            segs, words, detected = m_tr.transcribe_with_groq(audio, "en")

        self.assertEqual([x.text for x in segs],
                         [f"qism {i}" for i in range(5)])
        self.assertEqual([x.start for x in segs], [1.0, 61.0, 121.0, 181.0, 241.0])
        self.assertEqual([w.word for w in words], [f"soz{i}" for i in range(5)])
        self.assertEqual(detected, "english")

    def test_one_failed_chunk_does_not_lose_the_rest(self):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "audio.webm"
            audio.write_bytes(b"x" * 100)
            self._stub(fail_at=120.0)   # 3-bo'lak tushadi
            os.environ["GROQ_AUDIO_WORKERS"] = "3"
            segs, _words, _detected = m_tr.transcribe_with_groq(audio, "en")

        texts = [x.text for x in segs]
        self.assertEqual(texts, ["qism 0", "qism 1", "qism 3", "qism 4"])
        self.assertNotIn("qism 2", texts)

    def test_single_worker_gives_the_same_result(self):
        import os

        results = {}
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "audio.webm"
            audio.write_bytes(b"x" * 100)
            for workers in ("1", "4"):
                self._stub()
                os.environ["GROQ_AUDIO_WORKERS"] = workers
                segs, _w, _d = m_tr.transcribe_with_groq(audio, "en")
                results[workers] = [(x.start, x.text) for x in segs]
        self.assertEqual(results["1"], results["4"])

    def test_chunk_files_are_cleaned_up(self):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "audio.webm"
            audio.write_bytes(b"x" * 100)
            self._stub()
            os.environ["GROQ_AUDIO_WORKERS"] = "3"
            m_tr.transcribe_with_groq(audio, "en")
            left = sorted(p.name for p in Path(tmp).iterdir())
        self.assertEqual(left, ["audio.webm"], f"vaqtinchalik fayl qoldi: {left}")


class ThreadSafetyTests(unittest.TestCase):
    """Parallel ishda umumiy holat buzilmasligi kerak."""

    def test_usage_counter_does_not_lose_increments(self):
        import threading

        dp.core.reset_usage()
        threads = [
            threading.Thread(target=lambda: [dp.core._count("translate") for _ in range(500)])
            for _ in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(dp.core.USAGE["translate"], 4000)
        dp.core.reset_usage()

    def test_emit_writes_whole_lines(self):
        """Ilova stdout'ni qator-qator JSON deb o'qiydi — qator bo'linmasin."""
        import io
        import json
        import sys
        import threading

        buffer = io.StringIO()
        real = sys.stdout
        sys.stdout = buffer
        try:
            threads = [
                threading.Thread(
                    target=lambda n=n: [
                        dp.emit("progress", message=f"oqim {n} xabar {i}", progress=0.5)
                        for i in range(100)
                    ]
                )
                for n in range(6)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            sys.stdout = real
        lines = [ln for ln in buffer.getvalue().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 600)
        for line in lines:
            json.loads(line)  # buzilgan qator bo'lsa shu yerda tushadi


class ProviderRetryTests(unittest.TestCase):
    """Qayta urinish siyosati — bu bevosita vaqt va pulga ta'sir qiladi.

    Ilgari sikl 5 marta x 4 provayder = bitta to'plam uchun 20 ta chaqiruv
    edi va har aylanishda 6 soniya kutilardi, hatto kalit yaroqsiz bo'lsa
    ham (ikkinchi urinish ham aynan o'sha "401" ni qaytaradi)."""

    def setUp(self):
        import os

        self._env = {
            k: os.environ.get(k)
            for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY")
        }
        for k in self._env:
            os.environ[k] = "test-key"
        self._real = {
            name: getattr(m_tx, f"translate_{name}")
            for name in ("openai", "claude", "gemini", "groq")
        }
        self._backoff = m_tx.ai_retry_backoff
        self._throttle = m_tx.ai_throttle
        # Testda kutmaymiz.
        m_tx.ai_retry_backoff = lambda attempt=0: None
        m_tx.ai_throttle = lambda: None
        dp.core.AI_DISABLED.clear()
        self.calls: dict[str, int] = {}

    def tearDown(self):
        import os

        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for name, fn in self._real.items():
            setattr(m_tx, f"translate_{name}", fn)
        m_tx.ai_retry_backoff = self._backoff
        m_tx.ai_throttle = self._throttle
        dp.core.AI_DISABLED.clear()

    def _stub(self, name: str, error: Exception | None = None, reply: str | None = None):
        def fake(_prompt: str, _payload: str) -> str:
            self.calls[name] = self.calls.get(name, 0) + 1
            if error is not None:
                raise error
            return reply or "{}"

        setattr(m_tx, f"translate_{name}", fake)

    def test_bad_key_is_tried_once_not_twenty_times(self):
        class AuthError(Exception):
            status_code = 401

        for name in ("openai", "claude", "gemini", "groq"):
            self._stub(name, AuthError("Incorrect API key provided"))
        out, provider = m_tx.ai_translate_batch(["Hello"], "uz", "en")
        self.assertEqual(provider, "offline_dictionary")
        for name, count in self.calls.items():
            self.assertEqual(count, 1, f"{name} {count} marta chaqirildi (1 bo'lishi kerak)")

    def test_disabled_provider_is_skipped_by_later_batches(self):
        class AuthError(Exception):
            status_code = 401

        for name in ("openai", "claude", "gemini", "groq"):
            self._stub(name, AuthError("invalid api key"))
        m_tx.ai_translate_batch(["Hello"], "uz", "en")
        first = dict(self.calls)
        m_tx.ai_translate_batch(["World"], "uz", "en")
        self.assertEqual(self.calls, first, "o'chirilgan provayder yana chaqirildi")
        self.assertEqual(len(dp.core.AI_DISABLED), 4)

    def test_rate_limit_is_retried(self):
        class RateLimit(Exception):
            status_code = 429

        for name in ("openai", "claude", "gemini", "groq"):
            self._stub(name, RateLimit("rate limit exceeded"))
        m_tx.ai_translate_batch(["Hello"], "uz", "en")
        # 3 urinish x 4 provayder, lekin hech biri o'chirilmaydi.
        self.assertEqual(self.calls["openai"], m_tx.ai_attempts())
        self.assertEqual(dp.core.AI_DISABLED, {})

    def test_decommissioned_model_is_not_retried(self):
        for name in ("openai", "claude", "gemini", "groq"):
            self._stub(name, Exception("llama-3.1-8b has been decommissioned"))
        m_tx.ai_translate_batch(["Hello"], "uz", "en")
        self.assertEqual(self.calls["openai"], 1)

    def test_bad_request_provider_returns_for_the_next_smaller_batch(self):
        """400 ba'zan "matn juda uzun" degani — to'plam bo'lingach yana ishlaydi.

        Shuning uchun `bad_request` provayderni butun ish davomiga EMAS,
        faqat shu chaqiruv ichida chetlab o'tadi."""
        for name in ("openai", "claude", "gemini", "groq"):
            self._stub(name, Exception("400 invalid request: context too long"))
        m_tx.ai_translate_batch(["Hello"], "uz", "en")
        self.assertEqual(dp.core.AI_DISABLED, {}, "provayder butunlay o'chirildi")
        before = self.calls["openai"]
        m_tx.ai_translate_batch(["World"], "uz", "en")
        self.assertGreater(
            self.calls["openai"], before,
            "keyingi (kichikroq) to'plamda provayder qayta sinalmadi",
        )

    def test_first_working_provider_wins_and_stops_the_loop(self):
        self._stub("openai", Exception("rate limit exceeded"))
        self._stub("claude", reply='{"0": "Salom"}')
        self._stub("gemini", reply='{"0": "XATO"}')
        out, provider = m_tx.ai_translate_batch(["Hello"], "uz", "en")
        self.assertEqual(out, ["Salom"])
        self.assertEqual(provider, "claude")
        self.assertNotIn("gemini", self.calls, "g'olib topilgandan keyin ham davom etdi")

    def test_backoff_grows_and_is_capped(self):
        import os

        slept: list[float] = []
        real_sleep = __import__("time").sleep
        __import__("time").sleep = lambda s: slept.append(s)
        old = {k: os.environ.get(k) for k in ("AI_RETRY_BACKOFF_SEC", "AI_RETRY_MAX_SEC")}
        os.environ["AI_RETRY_BACKOFF_SEC"] = "6"
        os.environ["AI_RETRY_MAX_SEC"] = "30"
        try:
            for attempt in range(4):
                dp.core.ai_retry_backoff(attempt)
        finally:
            __import__("time").sleep = real_sleep
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        # 6 -> 12 -> 24 -> 30 (chegara), ustiga kichik tasodifiy qo'shimcha
        self.assertAlmostEqual(slept[0], 6, delta=1.0)
        self.assertAlmostEqual(slept[1], 12, delta=1.5)
        self.assertAlmostEqual(slept[2], 24, delta=2.5)
        self.assertLessEqual(slept[3], 33)
        self.assertGreater(slept[1], slept[0], "backoff o'smadi")


if __name__ == "__main__":
    unittest.main()
