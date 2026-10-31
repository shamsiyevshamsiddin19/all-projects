"""Modullarga bo'lingan eksport qatlamlari uchun regressiya sinovlari."""
from __future__ import annotations

import unittest


class ModuleBoundaryTests(unittest.TestCase):
    def test_transcription_layers_and_legacy_import_share_api(self) -> None:
        import subtitr.transcribe as legacy
        from subtitr import transcribe_providers, transcribe_rescan, transcribe_vad

        self.assertTrue(callable(legacy.transcribe_with_groq))
        self.assertTrue(callable(transcribe_providers.groq_file))
        self.assertTrue(callable(transcribe_rescan.rescan_swallowed_speech))
        self.assertTrue(callable(transcribe_vad.speech_regions))

    def test_document_layers_and_legacy_import_share_api(self) -> None:
        import subtitr.documents as legacy
        from subtitr import documents_markdown, documents_pdf, documents_text

        self.assertTrue(callable(legacy.write_txt_vocab))
        self.assertTrue(callable(documents_text.write_csv_vocab))
        self.assertTrue(callable(documents_markdown.write_md_reading))
        self.assertTrue(callable(documents_pdf.write_pdf_reading))
