"""AI Dublyaj va ko'p tilli audio yo'lakchalari moduli uchun testlar."""
from __future__ import annotations

import sys
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr import dubbing as m_dub  # noqa: E402


class DubbingVoiceTests(TestCase):
    def test_resolve_voice_defaults(self):
        self.assertEqual(m_dub.resolve_voice(None, "uz"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice("sardor"), "uz-UZ-SardorNeural")
        self.assertEqual(m_dub.resolve_voice("madina"), "uz-UZ-MadinaNeural")
        self.assertEqual(m_dub.resolve_voice(None, "ru"), "ru-RU-DmitryNeural")
        self.assertEqual(m_dub.resolve_voice("custom-voice-neural"), "custom-voice-neural")


class DubbingTimelineTests(TestCase):
    def test_build_speech_timeline_writes_correct_duration_and_silence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            clip1 = tmp / "clip1.wav"
            # 1 second clip at 24000Hz 16-bit mono
            sample_rate = 24000
            with wave.open(str(clip1), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                f.writeframes(b"\x01\x00" * sample_rate)

            out_wav = tmp / "timeline.wav"
            # Clip starts at 2.0s, total duration is 5.0s
            m_dub.build_speech_timeline_wav(
                [(2.0, clip1)],
                total_duration=5.0,
                out_wav_path=out_wav,
                sample_rate=sample_rate,
            )

            with wave.open(str(out_wav), "rb") as f:
                n_frames = f.getnframes()
                self.assertEqual(n_frames, 5 * sample_rate)


class DubbingMuxingTests(TestCase):
    @patch.object(m_dub, "run", return_value=SimpleNamespace(returncode=0, stderr=""))
    @patch.object(m_dub, "require_tool")
    @patch.object(m_dub, "probe_audio_codec", return_value="aac")
    def test_create_dubbed_video_maps_multi_tracks(self, mock_codec, mock_req, mock_run):
        out_video = Path("/tmp/out_dubbed.mp4")
        m_dub.create_dubbed_video(
            video_path=Path("/tmp/src.mp4"),
            dubbed_audio_path=Path("/tmp/dub.aac"),
            out_video_path=out_video,
            target_lang="uz",
            multi_track=True,
        )

        cmd = mock_run.call_args[0][0]
        # Video copy
        self.assertIn("-c:v", cmd)
        self.assertEqual(cmd[cmd.index("-c:v") + 1], "copy")
        # Track 0: Original
        self.assertIn("title=Asl ovoz (Original)", "".join(cmd))
        # Track 1: Uzbek Dubbed
        self.assertIn("title=O'zbekcha AI Dublyaj", "".join(cmd))
        self.assertIn("default", cmd)


if __name__ == "__main__":
    import unittest
    unittest.main()
