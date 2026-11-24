"""Transkripsiya keshi va avtomatik tozalash uchun qat'iy sinovlar."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from subtitr import cache as m_cache
from subtitr.core import Segment, Word


class TestCacheModule(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="subtitr_test_cache_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cache_dir_for_deterministic(self):
        video = self.tmp / "sample.mp4"
        video.write_bytes(b"dummy video data")
        
        dir1 = m_cache.cache_dir_for(video)
        dir2 = m_cache.cache_dir_for(video)
        self.assertEqual(dir1, dir2)
        self.assertTrue(dir1.is_dir())

    def test_transcription_signature_changes_with_env(self):
        sig1 = m_cache.transcription_signature()
        old_val = os.getenv("WHISPER_MODEL", "")
        try:
            os.environ["WHISPER_MODEL"] = "custom-test-model-xyz"
            sig2 = m_cache.transcription_signature()
            self.assertNotEqual(sig1, sig2)
        finally:
            if old_val:
                os.environ["WHISPER_MODEL"] = old_val
            else:
                os.environ.pop("WHISPER_MODEL", None)

    def test_save_and_load_transcription_roundtrip(self):
        cdir = self.tmp / "test_cdir"
        cdir.mkdir()
        
        segs = [
            Segment(0.0, 2.5, "Salom dunyo", 0.98),
            Segment(2.5, 5.0, "Yangi qism", 0.85),
        ]
        words = [Word(0.0, 1.0, "Salom"), Word(1.0, 2.5, "dunyo")]
        
        m_cache.save_transcription(cdir, segs, words, "uz", "gemini")
        loaded = m_cache.load_transcription(cdir)
        self.assertIsNotNone(loaded)
        loaded_segs, loaded_words, lang, transcriber = loaded
        
        self.assertEqual(len(loaded_segs), 2)
        self.assertEqual(loaded_segs[0].text, "Salom dunyo")
        self.assertEqual(loaded_segs[0].confidence, 0.98)
        self.assertEqual(len(loaded_words), 2)
        self.assertEqual(lang, "uz")
        self.assertTrue(transcriber.endswith("+cache"))

    def test_corrupted_transcription_handled_gracefully(self):
        cdir = self.tmp / "bad_cdir"
        cdir.mkdir()
        tr_file = cdir / "transcription.json"
        
        # Buzilgan JSON
        tr_file.write_text("{bu: buzuq json...}", encoding="utf-8")
        self.assertIsNone(m_cache.load_transcription(cdir))
        
        # Noto'g'ri versiya
        tr_file.write_text(json.dumps({"v": 999, "segments": []}), encoding="utf-8")
        self.assertIsNone(m_cache.load_transcription(cdir))

    def test_cache_disabled_flag(self):
        cdir = self.tmp / "flag_cdir"
        cdir.mkdir()
        segs = [Segment(0.0, 1.0, "Test", 0.9)]
        
        old_flag = os.getenv("SUBTITR_NO_CACHE")
        try:
            os.environ["SUBTITR_NO_CACHE"] = "1"
            m_cache.save_transcription(cdir, segs, [], "uz", "test")
            self.assertFalse((cdir / "transcription.json").exists())
            self.assertIsNone(m_cache.load_transcription(cdir))
        finally:
            if old_flag is not None:
                os.environ["SUBTITR_NO_CACHE"] = old_flag
            else:
                os.environ.pop("SUBTITR_NO_CACHE", None)

    def test_prune_transcript_cache_lru(self):
        cdir = self.tmp / "transcripts_cache"
        cdir.mkdir()

        # 3 ta papka yaratamiz va har birining mtime ini har xil qilamiz
        d1 = cdir / "item1_old"
        d1.mkdir()
        (d1 / "tr.json").write_bytes(b"x" * 2000)
        os.utime(d1, (time.time() - 300, time.time() - 300))

        d2 = cdir / "item2_mid"
        d2.mkdir()
        (d2 / "tr.json").write_bytes(b"x" * 2000)
        os.utime(d2, (time.time() - 200, time.time() - 200))

        d3 = cdir / "item3_new"
        d3.mkdir()
        (d3 / "tr.json").write_bytes(b"x" * 2000)
        os.utime(d3, (time.time() - 50, time.time() - 50))

        # 1. max_dirs=2 qilib tozalash -> d1 o'chirilishi kerak (eng eski)
        freed = m_cache.prune_transcript_cache(cache_dir=cdir, max_dirs=2, max_total_bytes=100000)
        self.assertGreater(freed, 0)
        self.assertFalse(d1.exists())
        self.assertTrue(d2.exists())
        self.assertTrue(d3.exists())

        # 2. max_total_bytes=2500 qilib tozalash -> d2 ham o'chirilishi kerak
        freed2 = m_cache.prune_transcript_cache(cache_dir=cdir, max_dirs=10, max_total_bytes=2500)
        self.assertGreater(freed2, 0)
        self.assertFalse(d2.exists())
        self.assertTrue(d3.exists())


if __name__ == "__main__":
    unittest.main()

