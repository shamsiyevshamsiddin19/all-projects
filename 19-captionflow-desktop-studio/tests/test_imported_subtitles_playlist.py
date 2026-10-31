"""Tashqi subtitr importi va playlist tanlash kontraktlari."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from subtitr import media
from subtitr import pipeline
from subtitr.core import Segment


class ImportedSubtitleTests(unittest.TestCase):
    def test_ass_dialogue_keeps_commas_and_normalizes_breaks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "film.ass"
            path.write_text(
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                "Dialogue: 0,0:00:01.20,0:00:03.50,Default,,0,0,0,,Salom, dunyo\\Nqalay?\n",
                encoding="utf-8",
            )
            segments = media.parse_subtitle(path)
        self.assertEqual(len(segments), 1)
        self.assertAlmostEqual(segments[0].start, 1.2)
        self.assertAlmostEqual(segments[0].end, 3.5)
        self.assertEqual(segments[0].text, "Salom, dunyo qalay?")

    def test_unknown_import_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "notes.txt"
            path.write_text("hello", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SRT"):
                media.parse_subtitle(path)

    def test_global_offset_preserves_duration_and_clamps_negative_start(self) -> None:
        shifted = pipeline._apply_subtitle_offset(
            [Segment(1.0, 3.0, "kechroq"), Segment(0.0, 0.5, "tashlanadi")], -1.0
        )
        self.assertEqual(len(shifted), 1)
        self.assertEqual((shifted[0].start, shifted[0].end), (0.0, 2.0))


class PlaylistInspectionTests(unittest.TestCase):
    def test_playlist_is_listed_not_downloaded_and_is_limited(self) -> None:
        payload = {
            "entries": [
                {"id": "abc", "title": "Birinchi", "url": "abc", "duration": 42},
                {"id": "def", "title": "Ikkinchi", "webpage_url": "https://example.test/def"},
            ]
        }
        completed = subprocess.CompletedProcess(["yt-dlp"], 0, json.dumps(payload), "")
        with (
            patch.object(media, "YTDLP", "yt-dlp"),
            patch.object(media.shutil, "which", return_value="/usr/bin/yt-dlp"),
            patch.object(media, "js_runtime_args", return_value=[]),
            patch.object(media.subprocess, "run", return_value=completed) as run,
        ):
            entries = media.playlist_entries("https://youtube.test/playlist", limit=999)
        command = run.call_args.args[0]
        self.assertIn("--flat-playlist", command)
        self.assertIn("--dump-single-json", command)
        self.assertEqual(command[command.index("--playlist-end") + 1], "100")
        self.assertEqual(entries[0]["url"], "https://www.youtube.com/watch?v=abc")
        self.assertEqual(entries[1]["url"], "https://example.test/def")
