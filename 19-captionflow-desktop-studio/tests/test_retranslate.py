"""Regression tests for the one-line editor retranslation contract."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from subtitr.pipeline import retranslate_session_segment


class RetranslateSegmentTests(unittest.TestCase):
    def test_uses_only_requested_line_and_neighbour_context(self) -> None:
        session = {
            "sourceLang": "ru",
            "targetLang": "uz",
            "segments": [
                {"original": "oldingi"},
                {"original": "tarjima qil"},
                {"original": "keyingi"},
                {"original": "yana"},
            ],
        }
        with patch("subtitr.pipeline._load_session", return_value=session), patch(
            "subtitr.pipeline.ai_translate_batch", return_value=(["tayyor"], "claude")
        ) as translated:
            result = retranslate_session_segment("/tmp/session.json", 1, "/tmp/edits.json")

        self.assertEqual(result, {"index": 1, "translated": "tayyor", "provider": "claude"})
        translated.assert_called_once_with(
            ["tarjima qil"], "uz", source_lang="ru", before=["oldingi"], after=["keyingi", "yana"]
        )

    def test_rejects_empty_original_without_calling_provider(self) -> None:
        with patch("subtitr.pipeline._load_session", return_value={
            "segments": [{"original": "  "}], "targetLang": "uz",
        }), patch("subtitr.pipeline.ai_translate_batch") as translated:
            with self.assertRaisesRegex(RuntimeError, "Bo'sh"):
                retranslate_session_segment("/tmp/session.json", 0)
        translated.assert_not_called()
