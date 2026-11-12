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

    def test_engines_are_thin_facades_not_implementation_buckets(self) -> None:
        """Qatlamlar faqat nom bilan emas, kod joylashuvi bilan ham ajralsin."""
        from pathlib import Path
        from subtitr import _documents_engine, _transcribe_engine

        package = Path(_transcribe_engine.__file__).parent
        self.assertLess(len(Path(_transcribe_engine.__file__).read_text().splitlines()), 180)
        self.assertLess(len(Path(_documents_engine.__file__).read_text().splitlines()), 40)
        self.assertGreater(len((package / "transcribe_providers.py").read_text().splitlines()), 200)
        self.assertGreater(len((package / "documents_markdown.py").read_text().splitlines()), 400)
