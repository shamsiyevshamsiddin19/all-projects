"""ASS va ffmpeg filtridagi maxsus belgilar regressiyasi."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import subtitles as m_sub  # noqa: E402


class AssEscapingTests(unittest.TestCase):
    def test_backslash_controls_remain_visible_text(self):
        # Tarjima modeli bergan `\N` va `\h` ekran formatini boshqarmasligi kerak.
        escaped = m_sub.ass_escape("Yo'l \\N va \\h\n{izoh}")
        self.assertEqual(escaped, "Yo'l \\\\N va \\\\h\\N(izoh)")


class FilterEscapingTests(unittest.TestCase):
    def test_filter_separators_in_font_path_are_escaped(self):
        # Papka nomidagi ajratgichlar alohida ffmpeg filtri deb o'qilmasin.
        escaped = m_sub._filter_escape(r"C:\Shriftlar[bold],demo; O'Brien")
        self.assertEqual(escaped, "C\\:\\\\Shriftlar\\[bold\\]\\,demo\\; O\\'Brien")


if __name__ == "__main__":
    unittest.main()
