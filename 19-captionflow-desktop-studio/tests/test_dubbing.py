"""AI Dublyaj va ko'p tilli audio yo'lakchalari moduli uchun testlar."""
from __future__ import annotations

import sys
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import dubbing as m_dub  # noqa: E402
from subtitr import pipeline as m_pipe  # noqa: E402


class DubbingVoiceTests(TestCase):
    def test_resolve_voice_defaults(self):
        self.assertEqual(m_dub.resolve_voice(None, "uz"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice("sardor"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice("madina"), "uz-UZ-MadinaNeural")
        self.assertEqual(m_dub.resolve_voice(None, "ru"), "ru-RU-DmitryNeural")
        self.assertEqual(m_dub.resolve_voice(None, "tr"), "tr-TR-AhmetNeural")
        self.assertEqual(m_dub.resolve_voice(None, "en"), "en-US-GuyNeural")
        self.assertEqual(m_dub.resolve_voice(None, "kk"), "kk-KZ-DauletNeural")
        self.assertEqual(m_dub.resolve_voice("custom-voice-neural"), "custom-voice-neural")

    def test_resolve_voice_unknown_lang_falls_back(self):
        self.assertEqual(m_dub.resolve_voice(None, "unknown_lang"), "uz-UZ-SardorNeural")


class DubbingTimelineTests(TestCase):
    def test_build_speech_timeline_writes_correct_duration_and_silence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            clip1 = tmp / "clip1.wav"
            sample_rate = 24000
            with wave.open(str(clip1), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                f.writeframes(b"\x01\x00" * sample_rate)

            out_wav = tmp / "timeline.wav"
            m_dub.build_speech_timeline_wav(
                [(2.0, clip1)],
                total_duration=5.0,
                out_wav_path=out_wav,
                sample_rate=sample_rate,
            )

            with wave.open(str(out_wav), "rb") as f:
                n_frames = f.getnframes()
                self.assertEqual(n_frames, 5 * sample_rate)

    def test_build_speech_timeline_empty_clips_produces_pure_silence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            out_wav = tmp / "silent.wav"
            sample_rate = 24000
            m_dub.build_speech_timeline_wav(
                [],
                total_duration=3.0,
                out_wav_path=out_wav,
                sample_rate=sample_rate,
            )

            with wave.open(str(out_wav), "rb") as f:
                self.assertEqual(f.getnframes(), 3 * sample_rate)
                data = f.readframes(f.getnframes())
                self.assertTrue(all(b == 0 for b in data))

    def test_build_speech_timeline_handles_unsorted_and_overlapping_clips(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            sample_rate = 24000
            clip1 = tmp / "c1.wav"
            with wave.open(str(clip1), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                f.writeframes(b"\x01\x00" * int(sample_rate * 1.5))

            clip2 = tmp / "c2.wav"
            with wave.open(str(clip2), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                f.writeframes(b"\x02\x00" * int(sample_rate * 1.0))

            out_wav = tmp / "mixed.wav"
            # Unsorted input: 2.0s clip passed before 0.5s clip
            m_dub.build_speech_timeline_wav(
                [(2.0, clip2), (0.5, clip1)],
                total_duration=4.0,
                out_wav_path=out_wav,
                sample_rate=sample_rate,
            )

            with wave.open(str(out_wav), "rb") as f:
                self.assertEqual(f.getnframes(), 4 * sample_rate)

    def test_build_speech_timeline_does_not_shift_overlapping_clip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            sample_rate = 100
            first = tmp / "first.wav"
            second = tmp / "second.wav"
            for path, value, seconds in ((first, b"\x01\x00", 2), (second, b"\x02\x00", 1)):
                with wave.open(str(path), "wb") as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(sample_rate)
                    f.writeframes(value * (sample_rate * seconds))

            out_wav = tmp / "timeline.wav"
            m_dub.build_speech_timeline_wav(
                [(0.0, first), (1.0, second)],
                total_duration=3.0,
                out_wav_path=out_wav,
                sample_rate=sample_rate,
            )

            with wave.open(str(out_wav), "rb") as f:
                self.assertEqual(f.getnframes(), 3 * sample_rate)
                f.setpos(sample_rate)
                self.assertEqual(f.readframes(1), b"\x02\x00")

    def test_build_speech_timeline_ignores_missing_file_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            missing = tmp / "non_existent.wav"
            out_wav = tmp / "out.wav"
            m_dub.build_speech_timeline_wav(
                [(1.0, missing)],
                total_duration=2.0,
                out_wav_path=out_wav,
                sample_rate=24000,
            )
            with wave.open(str(out_wav), "rb") as f:
                self.assertEqual(f.getnframes(), 2 * 24000)


class DubbingSynthesisFailureTests(TestCase):
    @patch.object(m_dub, "generate_clip_sync", side_effect=RuntimeError("tarmoq yo'q"))
    def test_all_failed_tts_segments_abort_the_job(self, _mock_generate):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RuntimeError, "birorta ovoz qatori"):
                m_dub.synthesize_all_segments(
                    [{"start": 0, "end": 1, "translated": "Salom"}],
                    voice="uz-UZ-SardorNeural",
                    work_dir=Path(tmp_dir),
                )


class DubbingMixerTests(TestCase):
    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="")
    def test_mix_dubbed_soundtrack_silent_source_bypasses_amix(self, mock_codec, mock_req, mock_run):
        speech_wav = Path("/tmp/speech.wav")
        out_audio = Path("/tmp/mixed.aac")
        m_dub.mix_dubbed_soundtrack(Path("/tmp/silent_video.mp4"), speech_wav, out_audio, ducking_volume=0.18)

        cmd = mock_run.call_args[0][0]
        self.assertNotIn("-filter_complex", cmd)
        self.assertIn(str(speech_wav), cmd)

    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_mix_dubbed_soundtrack_zero_ducking_mutes_source(self, mock_codec, mock_req, mock_run):
        speech_wav = Path("/tmp/speech.wav")
        out_audio = Path("/tmp/mixed.aac")
        m_dub.mix_dubbed_soundtrack(Path("/tmp/video.mp4"), speech_wav, out_audio, ducking_volume=0.0)

        cmd = mock_run.call_args[0][0]
        self.assertNotIn("-filter_complex", cmd)

    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_mix_dubbed_soundtrack_normal_ducking_applies_amix(self, mock_codec, mock_req, mock_run):
        speech_wav = Path("/tmp/speech.wav")
        out_audio = Path("/tmp/mixed.aac")
        m_dub.mix_dubbed_soundtrack(Path("/tmp/video.mp4"), speech_wav, out_audio, ducking_volume=0.25)

        cmd = mock_run.call_args[0][0]
        self.assertIn("-filter_complex", cmd)
        filter_str = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("volume=0.25", filter_str)
        self.assertIn("amix=inputs=2", filter_str)


class DubbingMuxingTests(TestCase):
    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_stream_count", return_value=2)
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_maps_multi_tracks(self, mock_codec, mock_count, mock_req, mock_run):
        out_video = Path("/tmp/out_dubbed.mp4")
        m_dub.create_dubbed_video(
            video_path=Path("/tmp/src.mp4"),
            dubbed_audio_path=Path("/tmp/dub.aac"),
            out_video_path=out_video,
            target_lang="uz",
            source_lang="ru",
            multi_track=True,
        )

        cmd = mock_run.call_args[0][0]
        # Video copy
        self.assertIn("-c:v", cmd)
        self.assertEqual(cmd[cmd.index("-c:v") + 1], "copy")
        # Track 0: Original
        self.assertIn("title=Asl ovoz (Original)", "".join(cmd))
        # Two original tracks are kept; Uzbek dub becomes track 2.
        self.assertIn("0:a?", cmd)
        self.assertIn("language=ru", "".join(cmd))
        self.assertIn("-metadata:s:a:2", cmd)
        self.assertIn("title=O'zbekcha AI Dublyaj", "".join(cmd))
        self.assertIn("default", cmd)

    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_with_subtitle_track_mp4(self, mock_codec, mock_req, mock_run):
        with tempfile.NamedTemporaryFile(suffix=".ass") as f_sub:
            sub_path = Path(f_sub.name)
            out_video = Path("/tmp/out_dubbed.mp4")
            m_dub.create_dubbed_video(
                video_path=Path("/tmp/src.mp4"),
                dubbed_audio_path=Path("/tmp/dub.aac"),
                out_video_path=out_video,
                ass_subtitle_path=sub_path,
                target_lang="uz",
                multi_track=True,
            )

            cmd = mock_run.call_args[0][0]
            self.assertIn("-c:s", cmd)
            self.assertEqual(cmd[cmd.index("-c:s") + 1], "mov_text")
            self.assertIn("title=O'zbekcha subtitr", "".join(cmd))

    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_with_subtitle_track_mkv(self, mock_codec, mock_req, mock_run):
        with tempfile.NamedTemporaryFile(suffix=".ass") as f_sub:
            sub_path = Path(f_sub.name)
            out_video = Path("/tmp/out_dubbed.mkv")
            m_dub.create_dubbed_video(
                video_path=Path("/tmp/src.mkv"),
                dubbed_audio_path=Path("/tmp/dub.aac"),
                out_video_path=out_video,
                ass_subtitle_path=sub_path,
                target_lang="uz",
                multi_track=True,
            )

            cmd = mock_run.call_args[0][0]
            self.assertIn("-c:s", cmd)
            self.assertEqual(cmd[cmd.index("-c:s") + 1], "copy")

    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="")
    def test_create_dubbed_video_source_without_audio_only_adds_dub(self, mock_codec, mock_req, mock_run):
        out_video = Path("/tmp/out_dubbed.mp4")
        m_dub.create_dubbed_video(
            video_path=Path("/tmp/silent.mp4"),
            dubbed_audio_path=Path("/tmp/dub.aac"),
            out_video_path=out_video,
            target_lang="uz",
            multi_track=True,
        )

        cmd = mock_run.call_args[0][0]
        self.assertNotIn("title=Asl ovoz (Original)", "".join(cmd))
        self.assertIn("title=O'zbekcha AI Dublyaj", "".join(cmd))


class DubbingSynthesisTests(TestCase):
    @patch.object(m_dub, "adjust_audio_tempo", return_value=1.5)
    @patch.object(m_dub, "generate_clip_sync")
    def test_synthesize_all_segments_handles_dict_and_dataclass(self, mock_gen, mock_tempo):
        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = Path(tmp_dir)
            dict_seg = {"start": 0.0, "end": 2.0, "translated": "Salom dunyo"}
            obj_seg = SimpleNamespace(start=3.0, end=5.0, translated="Xush kelibsiz")
            empty_seg = {"start": 6.0, "end": 7.0, "translated": "   "}

            results = m_dub.synthesize_all_segments(
                [dict_seg, obj_seg, empty_seg],
                voice="uz-UZ-SardorNeural",
                work_dir=work_dir,
            )

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0][0], 0.0)
            self.assertEqual(results[1][0], 3.0)


class DubbingPipelineIntegrationTests(TestCase):
    def test_dubbing_mode_is_registered_in_video_modes(self):
        self.assertIn("dubbing", m_pipe.VIDEO_MODES)

    def test_dubbing_mode_requires_translation(self):
        job = {
            "video": "source.mp4",
            "stem": "source",
            "mode": "dubbing",
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
            source = Path(raw_dir) / "source.mp4"
            source.touch()
            job["video"] = str(source)
            with (
                patch.object(m_pipe, "OUT_DIR", Path(raw_dir)),
                patch.object(m_pipe, "ensure_dirs"),
                patch.object(m_pipe, "require_tool"),
                patch.object(m_pipe, "require_disk_space"),
                patch.object(m_pipe, "emit"),
                patch.object(m_pipe, "_write_mode_ass"),
                patch.object(m_dub, "synthesize_all_segments", return_value=[(0.0, Path("/tmp/dummy.wav"))]),
                patch.object(m_dub, "build_speech_timeline_wav"),
                patch.object(m_dub, "mix_dubbed_soundtrack"),
                patch.object(m_dub, "create_dubbed_video") as mock_create,
            ):
                result = m_pipe._render_outputs(job)

        mock_create.assert_called_once()
        self.assertIsNone(mock_create.call_args.kwargs["ass_subtitle_path"])
        self.assertEqual(result["outputs"][-1]["kind"], "video")


if __name__ == "__main__":
    import unittest
    unittest.main()
