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


if __name__ == "__main__":
    unittest.main()
