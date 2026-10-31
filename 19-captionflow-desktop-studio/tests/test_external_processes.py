"""Tashqi dastur va servis chegaralari uchun regressiya testlari.

Bu testlar haqiqiy ffmpeg, yt-dlp yoki Groq tarmog'iga chiqmaydi. Ularning
o'rniga jarayonning stdout/stderr oqimini beradigan kichik soxta obyektlar
ishlatiladi. Shuning uchun test tez, bepul va xato yo'llarini ham aniq
tekshiradi.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import media as m_media  # noqa: E402
from subtitr import subtitles as m_sub  # noqa: E402
from subtitr import transcribe as m_tr  # noqa: E402
from subtitr.core import Segment, Word  # noqa: E402


class FakePopen:
    """`Popen`ning aynan tekshirilayotgan ikki oqimini taqlid qiladi."""

    def __init__(self, lines: list[str], returncode: int, stderr: str = ""):
        self.stdout = io.StringIO("".join(lines))
        self.stderr = io.StringIO(stderr)
        self.returncode = returncode
        self.wait_count = 0

    def wait(self) -> int:
        self.wait_count += 1
        return self.returncode


class BurnSubtitlesProcessTests(unittest.TestCase):
    def test_failed_ffmpeg_return_code_removes_partial_video_and_reports_stderr(self):
        """Noto'g'ri kod qaytsa, yarim MP4 foydalanuvchiga tayyor deb ko'rinmasin."""
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            video = directory / "source.mp4"
            ass = directory / "captions.ass"
            output = directory / "ready.mp4"
            video.write_bytes(b"source")
            ass.write_text("[Events]\n", encoding="utf-8")
            # Soxta ffmpeg allaqachon fayl yaratib ulgurgan holatni sinaymiz.
            output.write_bytes(b"broken partial video")

            calls: list[tuple[list[str], dict[str, object]]] = []

            def fake_popen(cmd: list[str], *args: object, **kwargs: object) -> FakePopen:
                calls.append((cmd, kwargs))
                return FakePopen(
                    ["out_time_us=5000000\n"],
                    returncode=23,
                    stderr="encoder rejected this test stream\n",
                )

            cpu = m_sub.EncoderChoice(
                "libx264", ["-preset", "veryfast", "-crf", "20"], "libx264 (CPU)"
            )
            with (
                patch.object(m_sub, "require_tool"),
                patch.object(m_sub, "probe_duration_seconds", return_value=10.0),
                patch.object(m_sub, "audio_args_for", return_value=["-c:a", "aac", "-b:a", "128k"]),
                patch.object(m_sub, "pick_video_encoder", return_value=cpu),
                patch.object(m_sub.subprocess, "Popen", side_effect=fake_popen),
                patch.object(m_sub, "emit") as emit,
            ):
                with self.assertRaisesRegex(RuntimeError, "encoder rejected this test stream"):
                    m_sub.burn_subtitles(video, ass, output, label="uzbekcha")

        # Muammo yuz bersa tozalash bajarilganini faqat mock emas, haqiqiy
        # vaqtinchalik fayl bilan tekshiramiz; `discard_partial()` yo'qolsa ushlaydi.
        self.assertFalse(output.exists())
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertEqual(kwargs["cwd"], str(ass.parent))
        self.assertEqual(command[command.index("-c:v") + 1], "libx264")
        self.assertEqual(command[command.index("-progress") + 1], "pipe:1")
        self.assertIn(f"ass={ass.name}", command[command.index("-vf") + 1])
        # Jarayonning progress oqimi ham iste'mol qilinsin, aks holda haqiqiy
        # ffmpeg uzoq renderda stdout buferiga to'lib qolishi mumkin.
        self.assertTrue(any("50%" in str(call) for call in emit.call_args_list))

    def test_audio_copy_failure_retries_once_with_aac(self):
        """MP4 muxeri ko'chirishni rad etsa, video renderi bekorga to'xtamasin."""
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            video, ass, output = directory / "source.mp4", directory / "captions.ass", directory / "ready.mp4"
            video.write_bytes(b"source")
            ass.write_text("[Events]\n", encoding="utf-8")
            calls: list[list[str]] = []
            procs = [
                FakePopen([], returncode=1, stderr="audio stream cannot be copied\n"),
                FakePopen([], returncode=0),
            ]

            def fake_popen(cmd: list[str], *args: object, **kwargs: object) -> FakePopen:
                calls.append(cmd)
                return procs.pop(0)

            cpu = m_sub.EncoderChoice("libx264", ["-crf", "20"], "libx264 (CPU)")
            with (
                patch.object(m_sub, "require_tool"),
                patch.object(m_sub, "probe_duration_seconds", return_value=0.0),
                patch.object(m_sub, "audio_args_for", return_value=["-c:a", "copy"]),
                patch.object(m_sub, "pick_video_encoder", return_value=cpu),
                patch.object(m_sub.subprocess, "Popen", side_effect=fake_popen),
                patch.object(m_sub, "emit"),
            ):
                m_sub.burn_subtitles(video, ass, output)

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][calls[0].index("-c:a") + 1], "copy")
        self.assertEqual(calls[1][calls[1].index("-c:a") + 1], "aac")


class DownloadVideoProcessTests(unittest.TestCase):
    def test_youtube_retry_uses_fallback_client_and_returns_reported_video(self):
        """Birinchi YouTube klienti bloklansa, keyingi klient ishlashi kerak."""
        url = "https://www.youtube.com/watch?v=retry-demo"
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            key = m_media.download_cache_key(url)
            downloaded = directory / f"Video__{key}.mp4"
# deferred write
            calls: list[list[str]] = []
            processes = [
                FakePopen(["ERROR: first client is blocked\n"], returncode=1),
                FakePopen(["[download] 50.0%\n", f"{downloaded}\n"], returncode=0),
            ]

            def fake_popen(cmd: list[str], *args: object, **kwargs: object) -> FakePopen:
                calls.append(cmd)
                p = processes.pop(0)
                if p.returncode == 0: downloaded.write_bytes(b"complete video")
                return p

            with (
                patch.object(m_media, "YTDLP", "fake-yt-dlp"),
                patch.object(m_media, "FFMPEG", "fake-ffmpeg"),
                patch.object(m_media.shutil, "which", return_value="/usr/bin/fake-yt-dlp"),
                patch.object(m_media, "js_runtime_args", return_value=[]),
                patch.object(m_media.subprocess, "Popen", side_effect=fake_popen),
                patch.object(m_media, "prune_download_cache") as prune,
                patch.object(m_media, "emit") as emit,
            ):
                result = m_media.download_video(url, dest_dir=directory)

        self.assertEqual(result, downloaded)
        self.assertEqual(len(calls), 2)
        self.assertIn("youtube:player_client=android", calls[1])
        self.assertEqual(calls[1][calls[1].index("--ffmpeg-location") + 1], ".")
        prune.assert_called_once_with(directory, keep=downloaded)
        self.assertTrue(any("50%" in str(call) for call in emit.call_args_list))

    def test_failed_ytdlp_return_code_includes_tail_and_never_claims_success(self):
        """yt-dlp chiqish kodi nol bo'lmasa, bo'sh yo'l video deb qaytmasin."""
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            fake = FakePopen(["ERROR: geo restriction\n"], returncode=7)
            with (
                patch.object(m_media, "YTDLP", "fake-yt-dlp"),
                patch.object(m_media, "FFMPEG", "fake-ffmpeg"),
                patch.object(m_media.shutil, "which", return_value="/usr/bin/fake-yt-dlp"),
                patch.object(m_media, "js_runtime_args", return_value=[]),
                patch.object(m_media.subprocess, "Popen", return_value=fake) as popen,
                patch.object(m_media, "emit") as emit,
            ):
                with self.assertRaisesRegex(RuntimeError, "geo restriction"):
                    m_media.download_video("https://vimeo.example/video", dest_dir=directory)

        popen.assert_called_once()
        self.assertFalse(any("Video yuklandi" in str(call) for call in emit.call_args_list))


class GroqTranscriptionContractTests(unittest.TestCase):
    @staticmethod
    def _groq_module(created: list[object]) -> types.ModuleType:
        """Import qilinadigan `groq` modulini tarmoqqa chiqmaydigan nusxaga almashtiradi."""
        module = types.ModuleType("groq")

        class FakeGroq:
            def __init__(self, api_key: str):
                self.api_key = api_key
                created.append(self)

        module.Groq = FakeGroq
        return module

    def test_small_audio_uses_fake_client_then_rescans_same_result(self):
        """Kichik audio bir API so'roviga o'tib, qayta ko'rish qatlamidan o'tsin."""
        with tempfile.TemporaryDirectory() as raw_dir:
            audio = Path(raw_dir) / "speech.ogg"
            source = Path(raw_dir) / "source.mp4"
            audio.write_bytes(b"short audio")
            source.write_bytes(b"source")
            created: list[object] = []
            decoded = MagicMock(
                return_value=(
                    [Segment(0.0, 1.0, "Salom")],
                    [Word(0.0, 0.4, "Salom")],
                    "uzbek",
                )
            )
            rescan = MagicMock(side_effect=lambda _fn, _audio, _lang, segs, words, _source: (segs, words))
            with (
                patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}, clear=False),
                patch.dict(sys.modules, {"groq": self._groq_module(created)}),
                patch.object(m_tr, "model_candidates", return_value=["whisper-test"]),
                patch.object(m_tr, "_groq_transcribe_file", decoded),
                patch.object(m_tr, "rescan_swallowed_speech", rescan),
            ):
                segments, words, detected = m_tr.transcribe_with_groq(audio, "uz", source)

            # Soxta mijozning o'zi bilan ishlash API kaliti noto'g'ri obyektga
            # uzatilishi yoki haqiqiy SDK importi tasodifan qaytishini ushlaydi.
            self.assertEqual(len(created), 1)
            self.assertEqual(created[0].api_key, "fake-key")
            decoded.assert_called_once_with(created[0], ["whisper-test"], audio, "uz", 0.0)
            rescan.assert_called_once()
            self.assertEqual(rescan.call_args.args[5], source)
            self.assertEqual([item.text for item in segments], ["Salom"])
            self.assertEqual([item.word for item in words], ["Salom"])
            self.assertEqual(detected, "uzbek")

    def test_missing_key_fails_before_creating_any_client(self):
        """Kalitsiz holat tarmoqqa chiqish urinishidan oldin tushunarli to'xtaydi."""
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "GROQ_API_KEY topilmadi"):
                m_tr.transcribe_with_groq(Path("not-used.ogg"), "auto")

    def test_failed_chunk_return_code_leaves_no_chunk_file(self):
        """ffmpeg bo'lakni kesolmasa, vaqtinchalik `.ogg` qoldig'i qolmasin."""
        with tempfile.TemporaryDirectory() as raw_dir:
            audio = Path(raw_dir) / "long.ogg"
            audio.write_bytes(b"long enough for forced chunk mode")
            created: list[object] = []
            failed_cut = types.SimpleNamespace(returncode=1, stderr="cannot cut")
            with (
                patch.dict(
                    os.environ,
                    {
                        "GROQ_API_KEY": "fake-key",
                        "GROQ_AUDIO_CHUNK_BYTES": "1",
                        "GROQ_CHUNK_SECONDS": "60",
                        "GROQ_AUDIO_WORKERS": "1",
                    },
                    clear=False,
                ),
                patch.dict(sys.modules, {"groq": self._groq_module(created)}),
                patch.object(m_tr, "model_candidates", return_value=["whisper-test"]),
                patch.object(m_tr, "probe_duration_seconds", return_value=60.0),
                patch.object(m_tr, "run", return_value=failed_cut) as run,
                patch.object(
                    m_tr,
                    "rescan_swallowed_speech",
                    side_effect=lambda _fn, _audio, _lang, segs, words, _source: (segs, words),
                ),
                patch.object(m_tr, "emit") as emit,
            ):
                with self.assertRaises(RuntimeError):
                    m_tr.transcribe_with_groq(audio, "en")

            # verified raise
            self.assertEqual(run.call_args.args[0][0], m_tr.FFMPEG)
            self.assertFalse((audio.parent / "chunk_000.ogg").exists())
            self.assertTrue(any("audiosi kesilmadi" in str(call) for call in emit.call_args_list))


class AssWritingContractTests(unittest.TestCase):
    def test_ass_output_escapes_control_text_and_keeps_dual_lines_together(self):
        """ASS matni libass buyrug'iga aylanmasin, asl va tarjima bitta hodisada qolsin."""
        destination = Path("captions.ass")
        opened = mock_open()
        with patch.object(Path, "open", opened):
            m_sub.write_ass(
                destination,
                [Segment(0.0, 2.0, r"Asl {teg} C:\N")],
                [Segment(0.0, 2.0, "Tarjima")],
                None,
                {},
                1280,
                720,
            )

        rendered = "".join(call.args[0] for call in opened().write.call_args_list)
        self.assertIn("PlayResX: 1280", rendered)
        self.assertIn("PlayResY: 720", rendered)
        self.assertNotIn("{teg}", rendered)
        self.assertIn("Asl (teg) C:\\\u200bN", rendered)
        expected_event = (
            "Dialogue: 0,0:00:00.00,0:00:02.00,Bottom,,0,0,0,,"
            "{\\c&HFFFFFF&}Asl (teg) C:\\\u200bN\\N{\\c&H80E6FF&}Tarjima\n"
        )
        self.assertIn(expected_event, rendered)

    def test_translation_only_mode_does_not_leak_original_text(self):
        """"Faqat tarjima" rejimi asl gapni yashiradi, tarjima rangini esa saqlaydi."""
        destination = Path("translation-only.ass")
        opened = mock_open()
        with patch.object(Path, "open", opened):
            m_sub.write_ass(
                destination,
                [Segment(0.0, 1.0, "Hidden original")],
                [Segment(0.0, 1.0, "Ko'rinadigan tarjima")],
                None,
                {},
                1280,
                720,
                show_original=False,
                trans_color="#12AB34",
            )

        rendered = "".join(call.args[0] for call in opened().write.call_args_list)
        self.assertNotIn("Hidden original", rendered)
        self.assertIn("{\\c&H34AB12&}Ko'rinadigan tarjima", rendered)


if __name__ == "__main__":
    unittest.main()
