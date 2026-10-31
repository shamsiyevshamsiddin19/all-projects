"""Lug'at CSV eksporti uchun regressiya testlari."""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from subtitr.documents import write_csv_vocab  # noqa: E402


class VocabCsvExportTests(unittest.TestCase):
    def test_csv_has_flashcard_columns_and_merges_lemma_frequency(self):
        entries = [
            {"word": "qildim", "lemma": "qilmoq", "translation": "bajarmoq", "pos": "verb", "count": 2},
            {"word": "qildi", "lemma": "qilmoq", "translation": "bajarmoq", "pos": "verb", "count": 3},
            {"word": "kitob", "translation": "book, volume", "pos": "noun", "count": 1},
        ]
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "lugat.csv"
            write_csv_vocab(path, entries)
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))

        # Anki/Quizlet ustunlarni sarlavha bo'yicha tanlay olishi uchun ular
        # har safar bir xil tartibda va maxsus belgilarsiz yozilishi kerak.
        self.assertEqual(rows[0], ["So'z", "Tarjima", "So'z turkumi", "Chastota"])
        self.assertEqual(rows[1], ["qilmoq", "bajarmoq", "Fe'l", "5"])
        self.assertEqual(rows[2], ["kitob", "book, volume", "Ot", "1"])


if __name__ == "__main__":
    unittest.main()
