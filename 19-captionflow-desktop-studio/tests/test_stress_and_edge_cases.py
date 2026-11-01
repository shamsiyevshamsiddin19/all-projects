"""Keng ko'lamli stress va chegara holatlari (edge cases) test to'plami.

Ilovaning barcha qismlarini (audio ducking, Edge-TTS, timeline, muxing,
subtitrlar, CLI, sessiyalar) ekstremal sharoitlarda sinovdan o'tkazadi.
"""

from __future__ import annotations

import io
import json
import struct
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import subtitr.cli as m_cli
import subtitr.dubbing as m_dub
import subtitr.media as m_media
import subtitr.pipeline as m_pipe
import subtitr.subtitles as m_sub


def _create_dummy_wav(path: Path, duration_sec: float = 1.0, sample_rate: int = 24000) -> Path:
    """Haqiqiy test WAV faylini xotirada yaratadi."""
    path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        for i in range(num_samples):
            val = int(10000 * (1 if (i % 50) < 25 else -1))
            data.extend(struct.pack("<h", val))
        wf.writeframes(bytes(data))
    return path


class DubbingTimelineStressTests(TestCase):
    """Ovozli taymline va WAV sintezining ekstremal sharoitlardagi testlari."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="timeline_stress_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_clips_generates_pure_silence_wav(self):
        out = self.tmp / "silence.wav"
        m_dub.build_speech_timeline_wav([], total_duration=3.0, out_wav_path=out, sample_rate=24000)
        self.assertTrue(out.exists())
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getframerate(), 24000)
            self.assertEqual(wf.getnframes(), 3 * 24000)

    def test_zero_duration_empty_clips(self):
        out = self.tmp / "zero.wav"
        m_dub.build_speech_timeline_wav([], total_duration=0.0, out_wav_path=out, sample_rate=24000)
        self.assertTrue(out.exists())
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 0)

    def test_single_clip_at_zero(self):
        c1 = _create_dummy_wav(self.tmp / "c1.wav", duration_sec=1.0)
        out = self.tmp / "single.wav"
        m_dub.build_speech_timeline_wav([(0.0, c1)], total_duration=2.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 2 * 24000)

    def test_clip_with_negative_timestamp_clamped(self):
        c1 = _create_dummy_wav(self.tmp / "c1.wav", duration_sec=1.0)
        out = self.tmp / "neg.wav"
        m_dub.build_speech_timeline_wav([(-1.5, c1)], total_duration=2.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 2 * 24000)

    def test_fifty_rapid_clips_in_succession(self):
        clips = []
        for i in range(50):
            p = _create_dummy_wav(self.tmp / f"clip_{i:03d}.wav", duration_sec=0.1)
            clips.append((i * 0.1, p))
        out = self.tmp / "fifty.wav"
        m_dub.build_speech_timeline_wav(clips, total_duration=5.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 5 * 24000)

    def test_hundred_clips_shuffled_order(self):
        import random
        clips = []
        for i in range(100):
            p = _create_dummy_wav(self.tmp / f"c_{i:03d}.wav", duration_sec=0.05)
            clips.append((i * 0.1, p))
        shuffled = list(clips)
        random.shuffle(shuffled)
        out = self.tmp / "shuffled.wav"
        m_dub.build_speech_timeline_wav(shuffled, total_duration=10.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 10 * 24000)

    def test_massive_gap_between_clips(self):
        c1 = _create_dummy_wav(self.tmp / "c1.wav", duration_sec=1.0)
        c2 = _create_dummy_wav(self.tmp / "c2.wav", duration_sec=1.0)
        out = self.tmp / "gap.wav"
        m_dub.build_speech_timeline_wav([(0.0, c1), (50.0, c2)], total_duration=52.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 52 * 24000)

    def test_missing_clip_file_gracefully_skipped(self):
        c1 = _create_dummy_wav(self.tmp / "c1.wav", duration_sec=1.0)
        missing = self.tmp / "ghost.wav"
        out = self.tmp / "missing.wav"
        m_dub.build_speech_timeline_wav([(0.0, c1), (2.0, missing)], total_duration=4.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 4 * 24000)

    def test_overlapping_clips_written_sequentially(self):
        c1 = _create_dummy_wav(self.tmp / "c1.wav", duration_sec=2.0)
        c2 = _create_dummy_wav(self.tmp / "c2.wav", duration_sec=2.0)
        out = self.tmp / "overlap.wav"
        m_dub.build_speech_timeline_wav([(0.0, c1), (1.0, c2)], total_duration=4.0, out_wav_path=out, sample_rate=24000)
        with wave.open(str(out), "rb") as wf:
            self.assertEqual(wf.getnframes(), 4 * 24000)


class DubbingTempoAndEdgeCasesTests(TestCase):
    """Audio tempo va TTS sintezi chegara holatlari."""

    @patch("subtitr.dubbing.probe_duration_seconds", return_value=2.0)
    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    def test_adjust_audio_tempo_clamped_at_max_2x(self, mock_req, mock_run, mock_dur):
        out = Path("/tmp/out.wav")
        m_dub.adjust_audio_tempo(Path("/tmp/in.mp3"), out, target_duration=0.5)
        cmd = mock_run.call_args[0][0]
        self.assertIn("atempo=2.000", cmd[cmd.index("-filter:a") + 1])

    @patch("subtitr.dubbing.probe_duration_seconds", return_value=0.5)
    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    def test_adjust_audio_tempo_clamped_at_min_075x(self, mock_req, mock_run, mock_dur):
        out = Path("/tmp/out.wav")
        m_dub.adjust_audio_tempo(Path("/tmp/in.mp3"), out, target_duration=2.0)
        cmd = mock_run.call_args[0][0]
        self.assertIn("atempo=0.750", cmd[cmd.index("-filter:a") + 1])

    @patch("subtitr.dubbing.probe_duration_seconds", return_value=1.0)
    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    def test_adjust_audio_tempo_normal_range(self, mock_req, mock_run, mock_dur):
        out = Path("/tmp/out.wav")
        m_dub.adjust_audio_tempo(Path("/tmp/in.mp3"), out, target_duration=0.7)
        cmd = mock_run.call_args[0][0]
        self.assertIn("atempo=1.429", cmd[cmd.index("-filter:a") + 1])

    @patch("subtitr.dubbing.probe_duration_seconds", return_value=1.0)
    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    def test_adjust_audio_tempo_matching_duration_no_filter(self, mock_req, mock_run, mock_dur):
        out = Path("/tmp/out.wav")
        m_dub.adjust_audio_tempo(Path("/tmp/in.mp3"), out, target_duration=1.0)
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("-filter:a", cmd)

    @patch("subtitr.dubbing.probe_duration_seconds", return_value=0.01)
    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    def test_adjust_audio_tempo_extremely_short_probe(self, mock_req, mock_run, mock_dur):
        out = Path("/tmp/out.wav")
        m_dub.adjust_audio_tempo(Path("/tmp/in.mp3"), out, target_duration=1.0)
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("-filter:a", cmd)


class DubbingMixerAndMuxingTests(TestCase):
    """Audio ducking va video muxing testlari."""

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="aac")
    def test_ducking_volume_clamped_extremes(self, mock_codec, mock_req, mock_run):
        m_dub.mix_dubbed_soundtrack(Path("/tmp/v.mp4"), Path("/tmp/s.wav"), Path("/tmp/out.aac"), ducking_volume=-0.5)
        self.assertNotIn("-filter_complex", mock_run.call_args[0][0])

        m_dub.mix_dubbed_soundtrack(Path("/tmp/v.mp4"), Path("/tmp/s.wav"), Path("/tmp/out.aac"), ducking_volume=3.5)
        cmd = mock_run.call_args[0][0]
        self.assertIn("-filter_complex", cmd)
        self.assertIn("volume=1.00", cmd[cmd.index("-filter_complex") + 1])

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="aac")
    def test_ducking_channel_layouts_stereo(self, mock_codec, mock_req, mock_run):
        m_dub.mix_dubbed_soundtrack(Path("/tmp/v.mp4"), Path("/tmp/s.wav"), Path("/tmp/out.aac"), ducking_volume=0.18)
        cmd = mock_run.call_args[0][0]
        filter_str = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("aformat=channel_layouts=stereo", filter_str)
        self.assertIn("amix=inputs=2:duration=first", filter_str)

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_uzbek_title(self, mock_codec, mock_req, mock_run):
        out_v = Path("/tmp/out.mp4")
        m_dub.create_dubbed_video(Path("/tmp/in.mp4"), Path("/tmp/a.aac"), out_v, target_lang="uz", multi_track=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("title=O'zbekcha AI Dublyaj", cmd)
        self.assertIn("-metadata:s:a:1", cmd)
        self.assertIn("language=uz", cmd)

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_russian_title(self, mock_codec, mock_req, mock_run):
        out_v = Path("/tmp/out.mp4")
        m_dub.create_dubbed_video(Path("/tmp/in.mp4"), Path("/tmp/a.aac"), out_v, target_lang="ru", multi_track=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("title=AI Dublyaj (RU)", cmd)
        self.assertIn("language=ru", cmd)

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_turkish_title(self, mock_codec, mock_req, mock_run):
        out_v = Path("/tmp/out.mp4")
        m_dub.create_dubbed_video(Path("/tmp/in.mp4"), Path("/tmp/a.aac"), out_v, target_lang="tr", multi_track=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("title=AI Dublyaj (TR)", cmd)
        self.assertIn("language=tr", cmd)

    @patch("subtitr.dubbing.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.dubbing.require_tool")
    @patch("subtitr.dubbing.probe_audio_codec", return_value="")
    def test_create_dubbed_video_no_orig_audio_single_track(self, mock_codec, mock_req, mock_run):
        out_v = Path("/tmp/out.mp4")
        m_dub.create_dubbed_video(Path("/tmp/in.mp4"), Path("/tmp/a.aac"), out_v, target_lang="uz", multi_track=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("-map", cmd)
        self.assertIn("1:a", cmd)
        self.assertNotIn("-metadata:s:a:1", cmd)


class VoiceResolutionTests(TestCase):
    """Turli tillar uchun ovozlarni to'g'ri hal qilish testlari."""

    def test_resolve_default_voices(self):
        self.assertEqual(m_dub.resolve_voice(None, "uz"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice(None, "ru"), "ru-RU-DmitryNeural")
        self.assertEqual(m_dub.resolve_voice(None, "tr"), "tr-TR-AhmetNeural")
        self.assertEqual(m_dub.resolve_voice(None, "en"), "en-US-GuyNeural")
        self.assertEqual(m_dub.resolve_voice(None, "kk"), "kk-KZ-DauletNeural")
        self.assertEqual(m_dub.resolve_voice(None, "tg"), m_dub.DEFAULT_LANG_VOICES["tg"])
        self.assertEqual(m_dub.resolve_voice(None, "ky"), m_dub.DEFAULT_LANG_VOICES["ky"])

    def test_resolve_explicit_voice_override(self):
        self.assertEqual(m_dub.resolve_voice("uz-UZ-MadinaNeural", "uz"), "uz-UZ-MadinaNeural")
        self.assertEqual(m_dub.resolve_voice("ru-RU-SvetlanaNeural", "ru"), "ru-RU-SvetlanaNeural")

    def test_resolve_unknown_language_falls_back_to_uzbek(self):
        self.assertEqual(m_dub.resolve_voice(None, "zz"), "uz-UZ-SardorNeural")

    def test_resolve_voice_whitespace_handling(self):
        self.assertEqual(m_dub.resolve_voice("   ", "uz"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice("  uz-UZ-MadinaNeural  ", "uz"), "uz-UZ-MadinaNeural")


class SubtitleFormattingAndEdgeCasesTests(TestCase):
    """Subtitr matnlari va maxsus belgilar sinovlari."""

    def test_special_characters_in_srt(self):
        segs = [
            m_media.Segment(start=0.0, end=2.0, text="Salom & do'stlar <test> \"tirnoq\""),
            m_media.Segment(start=2.5, end=4.0, text="O'zbekiston, g'alaba, bog'cha, shahar"),
            m_media.Segment(start=4.5, end=6.0, text="Кирилл ёзуви: Ўзбекистон, Ғалаба, Қаҳрамон"),
        ]
        with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as f:
            p = Path(f.name)
        try:
            m_media.write_srt(p, segs)
            content = p.read_text(encoding="utf-8")
            self.assertIn("Salom & do'stlar <test> \"tirnoq\"", content)
            self.assertIn("O'zbekiston", content)
            self.assertIn("Кирилл ёзуви", content)
        finally:
            p.unlink(missing_ok=True)

    def test_empty_segments_list_srt(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as f:
            p = Path(f.name)
        try:
            m_media.write_srt(p, [])
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(encoding="utf-8"), "")
        finally:
            p.unlink(missing_ok=True)

    def test_sub_second_duration_segment(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as f:
            p = Path(f.name)
        try:
            m_media.write_srt(p, [m_media.Segment(start=1.000, end=1.050, text="Tez")])
            content = p.read_text(encoding="utf-8")
            self.assertIn("00:00:01,000 --> 00:00:01,050", content)
            self.assertIn("Tez", content)
        finally:
            p.unlink(missing_ok=True)

    def test_inverted_segment_start_greater_than_end(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as f:
            p = Path(f.name)
        try:
            m_media.write_srt(p, [m_media.Segment(start=5.0, end=3.0, text="Teskari")])
            self.assertTrue(p.exists())
        finally:
            p.unlink(missing_ok=True)

    def test_multiline_text_in_segment(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".srt", delete=False) as f:
            p = Path(f.name)
        try:
            m_media.write_srt(p, [m_media.Segment(start=0.0, end=2.0, text="Birinchi qator\nIkkinchi qator")])
            content = p.read_text(encoding="utf-8")
            self.assertIn("Birinchi qator", content)
            self.assertIn("Ikkinchi qator", content)
        finally:
            p.unlink(missing_ok=True)


class PipelineSoftsubAndDubbingTests(TestCase):
    """Pipeline rejimlarini ishga tushirish va renderlash testlari."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pipe_stress_"))
        self.dummy_video = self.tmp / "dummy.mp4"
        self.dummy_video.write_bytes(b"\x00" * 1024)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_softsub_dual_ass_creation(self):
        job = {
            "stem": "test_video",
            "video": str(self.dummy_video),
            "mode": "softsub",
            "sourceLang": "en",
            "targetLang": "uz",
            "transcriber": "whisper",
            "translator": "gemini",
            "width": 1280,
            "height": 720,
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Hello world", "translated": "Salom dunyo"},
                {"start": 2.5, "end": 5.0, "text": "How are you", "translated": "Qalaysiz"},
            ],
            "vocab": [],
        }

        with (
            patch.object(m_pipe, "ensure_dirs"),
            patch.object(m_pipe, "require_tool"),
            patch.object(m_pipe, "require_disk_space"),
            patch.object(m_pipe, "emit"),
            patch.object(m_pipe, "_write_mode_ass") as mock_write_ass,
            patch.object(m_pipe, "attach_soft_subtitles") as mock_attach,
        ):
            res = m_pipe._render_outputs(job)

        self.assertIn("outputs", res)
        self.assertGreaterEqual(mock_write_ass.call_count, 3)
        mock_attach.assert_called_once()
        kwargs = mock_attach.call_args[1]
        self.assertIsNotNone(kwargs.get("secondary_sub"))
        self.assertEqual(kwargs.get("title1"), "O'zbekcha (Tarjima)")
        self.assertEqual(kwargs.get("title2"), "Asl til (Original)")

    def test_dubbing_render_zero_ducking_volume(self):
        job = {
            "stem": "dub_test",
            "video": str(self.dummy_video),
            "mode": "dubbing",
            "sourceLang": "en",
            "targetLang": "uz",
            "transcriber": "whisper",
            "translator": "gemini",
            "width": 1280,
            "height": 720,
            "voice": "uz-UZ-MadinaNeural",
            "ducking": 0.0,
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Hello", "original": "Hello", "translated": "Salom"},
            ],
            "vocab": [],
        }

        with (
            patch.object(m_pipe, "ensure_dirs"),
            patch.object(m_pipe, "require_tool"),
            patch.object(m_pipe, "require_disk_space"),
            patch.object(m_pipe, "emit"),
            patch.object(m_pipe, "_write_mode_ass"),
            patch.object(m_pipe, "probe_duration_seconds", return_value=10.0),
            patch("subtitr.dubbing.synthesize_all_segments", return_value=[(0.0, Path("/tmp/seg.wav"))]),
            patch("subtitr.dubbing.build_speech_timeline_wav"),
            patch("subtitr.dubbing.mix_dubbed_soundtrack") as mock_mix,
            patch("subtitr.dubbing.create_dubbed_video") as mock_create,
        ):
            res = m_pipe._render_outputs(job)

        self.assertIn("outputs", res)
        mock_mix.assert_called_once()
        self.assertEqual(mock_mix.call_args[1].get("ducking_volume"), 0.0)
        mock_create.assert_called_once()


class CliArgumentParsingTests(TestCase):
    """CLI parametrlarining to'g'ri qabul qilinishi va tahlili testlari."""

    def test_cli_prepare_with_dubbing_mode(self):
        parser = m_cli.build_parser()
        args = parser.parse_args([
            "prepare", "--video", "/tmp/vid.mp4",
            "--mode", "dubbing",
            "--voice", "uz-UZ-MadinaNeural",
            "--ducking", "0.10",
        ])
        self.assertEqual(args.command, "prepare")
        self.assertEqual(args.mode, "dubbing")
        self.assertEqual(args.voice, "uz-UZ-MadinaNeural")
        self.assertEqual(args.ducking, 0.10)

    def test_cli_prepare_with_softsub_mode(self):
        parser = m_cli.build_parser()
        args = parser.parse_args([
            "prepare", "--video", "/tmp/vid.mp4",
            "--mode", "softsub",
        ])
        self.assertEqual(args.mode, "softsub")

    def test_cli_process_with_dubbing_and_ducking(self):
        parser = m_cli.build_parser()
        args = parser.parse_args([
            "process", "--video", "/tmp/vid.mp4",
            "--mode", "dubbing",
            "--ducking", "0.0",
        ])
        self.assertEqual(args.command, "process")
        self.assertEqual(args.mode, "dubbing")
        self.assertEqual(args.ducking, 0.0)

    def test_cli_render_default_arguments(self):
        parser = m_cli.build_parser()
        args = parser.parse_args(["render", "--session", "/tmp/sess.json"])
        self.assertEqual(args.command, "render")
        self.assertEqual(args.session, "/tmp/sess.json")
        self.assertEqual(args.font_scale, 1.0)
        self.assertEqual(args.position, "bottom")
        self.assertEqual(args.sub_color, "#FFE680")
        self.assertEqual(args.orig_style, "box")


class PipelinePreviewAndSubtitleFileStressTests(TestCase):
    """preview_frame va subtitle_file funksiyalarining chegara holatlari."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="preview_stress_"))
        self.dummy_video = self.tmp / "dummy.mp4"
        self.dummy_video.write_bytes(b"\x00" * 1024)
        self.session_file = self.tmp / "sess.json"
        session_data = {
            "sessionVersion": 2,
            "stem": "preview_sess",
            "video": str(self.dummy_video),
            "mode": "dual_vocab",
            "sourceLang": "en",
            "targetLang": "uz",
            "transcriber": "whisper",
            "translator": "gemini",
            "width": 1280,
            "height": 720,
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Hello", "original": "Hello", "translated": "Salom"},
                {"start": 2.5, "end": 4.5, "text": "World", "original": "World", "translated": "Dunyo"},
            ],
            "vocab": [{"word": "world", "translation": "dunyo", "start": 2.5, "end": 4.5}],
        }
        self.session_file.write_text(json.dumps(session_data), encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    @patch("subtitr.pipeline._write_mode_ass")
    def test_subtitle_file_generation_for_softsub(self, mock_write_ass):
        out_ass = self.tmp / "out_softsub.ass"
        res = m_pipe.subtitle_file(str(self.session_file), str(out_ass), render_mode="softsub")
        self.assertEqual(res["path"], str(out_ass))
        self.assertEqual(res["mode"], "softsub")
        mock_write_ass.assert_called_once()

    @patch("subtitr.pipeline._write_mode_ass")
    def test_subtitle_file_generation_for_dubbing(self, mock_write_ass):
        out_ass = self.tmp / "out_dub.ass"
        res = m_pipe.subtitle_file(str(self.session_file), str(out_ass), render_mode="dubbing")
        self.assertEqual(res["path"], str(out_ass))
        self.assertEqual(res["mode"], "dubbing")
        mock_write_ass.assert_called_once()

    @patch("subtitr.pipeline._write_mode_ass")
    def test_subtitle_file_custom_styling(self, mock_write_ass):
        out_ass = self.tmp / "out_styled.ass"
        m_pipe.subtitle_file(
            str(self.session_file), str(out_ass),
            font_scale=1.5, position="top", sub_color="#39FF14", orig_style="plain",
        )
        # _write_mode_ass argumentlarini tekshiramiz
        args = mock_write_ass.call_args[0]
        self.assertEqual(args[3], 1.5)  # font_scale
        self.assertEqual(args[4], "top")  # position
        self.assertEqual(args[5], "#39FF14")  # sub_color
        self.assertEqual(args[6], "plain")  # orig_style

    @patch("subtitr.pipeline.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.pipeline.require_tool")
    @patch("subtitr.pipeline._write_mode_ass")
    def test_preview_frame_negative_timestamp_clamped_to_zero(self, mock_write_ass, mock_req, mock_run):
        out_frame = self.tmp / "frame.jpg"
        out_frame.write_bytes(b"dummy_frame_bytes")
        res = m_pipe.preview_frame(str(self.session_file), at=-3.5, out_path=str(out_frame))
        self.assertEqual(res["at"], -3.5)
        # ffmpeg buyrug'ida -ss 0.000 bo'lishi kerak
        cmd = mock_run.call_args[0][0]
        ss_idx = cmd.index("-ss")
        self.assertEqual(cmd[ss_idx + 1], "0.000")

    @patch("subtitr.pipeline.run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch("subtitr.pipeline.require_tool")
    @patch("subtitr.pipeline._write_mode_ass")
    def test_preview_frame_beyond_duration(self, mock_write_ass, mock_req, mock_run):
        out_frame = self.tmp / "frame.jpg"
        out_frame.write_bytes(b"dummy_frame_bytes")
        res = m_pipe.preview_frame(str(self.session_file), at=9999.0, out_path=str(out_frame))
        self.assertEqual(res["path"], str(out_frame))


class RetranslateAndSessionRecoveryTests(TestCase):
    """Qayta tarjima va sessiyadan tiklash holatlari."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="retrans_stress_"))
        self.dummy_video = self.tmp / "dummy.mp4"
        self.dummy_video.write_bytes(b"\x00" * 1024)
        self.session_file = self.tmp / "sess.json"
        session_data = {
            "sessionVersion": 2,
            "stem": "retrans_sess",
            "video": str(self.dummy_video),
            "mode": "dual_vocab",
            "sourceLang": "en",
            "targetLang": "uz",
            "transcriber": "whisper",
            "translator": "gemini",
            "width": 1280,
            "height": 720,
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "First line", "original": "First line", "translated": "Birinchi qator"},
                {"start": 2.5, "end": 4.5, "text": "Second line", "original": "Second line", "translated": "Ikkinchi qator"},
            ],
            "vocab": [],
        }
        self.session_file.write_text(json.dumps(session_data), encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_retranslate_invalid_negative_index_raises(self):
        with self.assertRaises(RuntimeError):
            m_pipe.retranslate_session_segment(str(self.session_file), index=-1)

    def test_retranslate_out_of_bounds_index_raises(self):
        with self.assertRaises(RuntimeError):
            m_pipe.retranslate_session_segment(str(self.session_file), index=100)

    @patch("subtitr.pipeline.ai_translate_batch", return_value=(["Yangilangan tarjima"], "mock_provider"))
    def test_retranslate_valid_index_updates_and_returns(self, mock_trans):
        res = m_pipe.retranslate_session_segment(str(self.session_file), index=1)
        self.assertEqual(res["index"], 1)
        self.assertEqual(res["translated"], "Yangilangan tarjima")
        self.assertEqual(res["provider"], "mock_provider")


class QualityAndMediaResolutionTests(TestCase):
    """Video sifatlari va formatlarini aniqlash testlari."""

    def test_quality_heights_mapping(self):
        self.assertEqual(m_media.QUALITY_HEIGHTS["1080"], 1080)
        self.assertEqual(m_media.QUALITY_HEIGHTS["720"], 720)
        self.assertEqual(m_media.QUALITY_HEIGHTS["1440"], 1440)
        self.assertEqual(m_media.QUALITY_HEIGHTS["2160"], 2160)

    def test_quality_height_helper(self):
        self.assertEqual(m_media.quality_height("1080"), 1080)
        self.assertEqual(m_media.quality_height("720"), 720)
        self.assertEqual(m_media.quality_height(None), 1080)
        self.assertEqual(m_media.quality_height("original"), 1080)
