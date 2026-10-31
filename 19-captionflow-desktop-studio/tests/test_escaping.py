"""ASS va ffmpeg filtridagi maxsus belgilar regressiyasi."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import subtitles as m_sub  # noqa: E402


class AssEscapingTests(unittest.TestCase):
    @staticmethod
    def _render_pgm(text: str, directory: Path, name: str) -> tuple[int, int, bytes]:
        ass_path = directory / f"{name}.ass"
        frame_path = directory / f"{name}.pgm"
        ass_path.write_text(
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 960\n"
            "PlayResY: 180\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,DejaVu Sans,44,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,16,16,16,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{text}\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                m_sub.FFMPEG, "-y", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=960x180:d=1:r=1",
                "-vf", f"ass={m_sub._filter_escape(str(ass_path))}",
                "-frames:v", "1", "-c:v", "pgm", str(frame_path),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode:
            raise AssertionError(proc.stderr[-1000:] or "ffmpeg ASS render xato")
        magic, dimensions, max_value, pixels = frame_path.read_bytes().split(b"\n", 3)
        if magic != b"P5" or max_value != b"255":
            raise AssertionError("ffmpeg kutilgan PGM kadrini bermadi")
        width, height = (int(value) for value in dimensions.split())
        return width, height, pixels

    @unittest.skipUnless(shutil.which("ffmpeg"), "Render regressiyasi uchun ffmpeg/libass kerak")
    def test_backslash_controls_match_one_line_render_reference(self):
        source = r"Yo'l C:\Users\N va \n va \h"
        # Etalondagi U+200B faqat testning kutilgan PIXEL natijasini beradi;
        # satrni solishtirish libass parserining haqiqiy xatosini ushlamaydi.
        reference = "Yo'l C:\\Users\\\u200bN va \\\u200bn va \\\u200bh"
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            actual = self._render_pgm(m_sub.ass_escape(source), directory, "actual")
            expected = self._render_pgm(reference, directory, "reference")

        self.assertEqual(actual, expected)
        width, height, pixels = actual
        ink_rows = [
            y for y in range(height)
            if any(value > 24 for value in pixels[y * width:(y + 1) * width])
        ]
        # Ikki qatorga bo'linishning vertikal izi bitta 44px shrift qatoridan
        # ancha baland bo'ladi; shu tekshiruv `\N` va `\n` yutilganini ushlaydi.
        self.assertLess(max(ink_rows) - min(ink_rows), 65)


class FilterEscapingTests(unittest.TestCase):
    def test_filter_separators_in_font_path_are_escaped(self):
        # Papka nomidagi ajratgichlar alohida ffmpeg filtri deb o'qilmasin.
        escaped = m_sub._filter_escape(r"C:\Shriftlar[bold],demo; O'Brien")
        self.assertEqual(escaped, "C\\:\\\\Shriftlar\\[bold\\]\\,demo\\; O\\'Brien")


if __name__ == "__main__":
    unittest.main()
