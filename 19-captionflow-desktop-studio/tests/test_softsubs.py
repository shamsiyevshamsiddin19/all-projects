"""Softsub muxlashining sifatni saqlaydigan yo'li uchun testlar."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import cli as m_cli  # noqa: E402
from subtitr import pipeline as m_pipe  # noqa: E402
from subtitr import subtitles as m_sub  # noqa: E402


class SoftsubMuxTests(unittest.TestCase):
    def _attach(self, extension: str) -> list[str]:
        with (
            patch.object(m_sub, "require_tool"),
            patch.object(m_sub, "emit"),
            patch.object(
                m_sub,
                "run",
                return_value=SimpleNamespace(returncode=0, stderr=""),
            ) as run,
        ):
            m_sub.attach_soft_subtitles(
                Path("source.mp4"), Path("captions.ass"), Path(f"ready{extension}"),
            )
        return run.call_args.args[0]

    def test_mp4_copies_media_and_encodes_compatible_subtitle_track(self):
        cmd = self._attach(".mp4")
        # Video qayta kodlansa, softsub rejimining vaqt va sifat foydasi yo'qoladi.
        self.assertEqual(cmd[cmd.index("-c:v") + 1], "copy")
        self.assertEqual(cmd[cmd.index("-c:a") + 1], "copy")
        self.assertEqual(cmd[cmd.index("-c:s") + 1], "mov_text")
        self.assertIn("1:0", cmd)

    def test_mkv_keeps_ass_subtitle_stream_without_conversion(self):
        cmd = self._attach(".mkv")
        self.assertEqual(cmd[cmd.index("-c:s") + 1], "copy")


class SoftsubPipelineTests(unittest.TestCase):
    def test_softsub_mode_routes_mkv_to_fast_muxer(self):
        job = {
            "video": "source.mkv",
            "stem": "source",
            "mode": "softsub",
            "sourceLang": "en",
            "targetLang": "uz",
            "transcriber": "test",
            "translator": "test",
            "width": 1280,
            "height": 720,
            "segments": [{
                "start": 0.0, "end": 2.0, "rawEnd": 2.0,
                "original": "Hello", "translated": "Salom",
            }],
            "words": [],
            "vocab": [],
        }
        with tempfile.TemporaryDirectory() as raw_dir:
            source = Path(raw_dir) / "source.mkv"
            source.touch()
            job["video"] = str(source)
            with (
                patch.object(m_pipe, "OUT_DIR", Path(raw_dir)),
                patch.object(m_pipe, "ensure_dirs"),
                patch.object(m_pipe, "require_tool"),
                patch.object(m_pipe, "require_disk_space"),
                patch.object(m_pipe, "emit"),
                patch.object(m_pipe, "_write_mode_ass"),
                patch.object(m_pipe, "attach_soft_subtitles") as attach,
                patch.object(m_pipe, "burn_subtitles") as burn,
            ):
                result = m_pipe._render_outputs(job)

        self.assertIn("softsub", m_pipe.VIDEO_MODES)
        self.assertEqual(m_pipe.modes_for("softsub"), ["softsub"])
        attach.assert_called_once()
        self.assertEqual(attach.call_args.args[2].suffix, ".mkv")
        burn.assert_not_called()
        self.assertEqual(result["outputs"][-1]["kind"], "video")


class SoftsubCliTests(unittest.TestCase):
    def test_process_accepts_softsub_mode(self):
        with (
            patch.object(m_cli, "ensure_dirs"),
            patch.object(m_cli, "setup_logging"),
            patch.object(m_cli, "install_signal_handlers"),
            patch.object(m_cli, "clean_orphan_tmp"),
            patch.object(m_cli, "emit"),
            patch.object(m_cli, "process", return_value={}) as process,
            patch.object(sys, "argv", ["subtitr", "process", "--video", "source.mp4", "--mode", "softsub"]),
        ):
            self.assertEqual(m_cli.main(), 0)
        self.assertEqual(process.call_args.args[1], "softsub")


if __name__ == "__main__":
    unittest.main()
