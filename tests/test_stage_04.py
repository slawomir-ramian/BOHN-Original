from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_stage_04


EXPECTED = [
    "S-001", "S-002", "S-003", "S-004", "S-005", "S-006",
    "S-010", "S-011", "S-007", "S-008", "S-009",
]


class Stage04Tests(unittest.TestCase):
    def test_pdf_chronology_is_not_numeric_sort(self):
        self.assertEqual(run_stage_04.SOURCE_CHRONOLOGY, EXPECTED)
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row["chapter"] == "3"]
        self.assertEqual([row["id"] for row in rows], EXPECTED)

    def test_historical_hashes(self):
        for experiment_id in EXPECTED:
            base = ROOT / "experiments" / "03_sbohn" / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            text = (base / "historical" / "source_from_monograph.py").read_text(encoding="utf-8")
            digest = hashlib.sha256(text[:-1].encode("utf-8")).hexdigest()
            self.assertEqual(digest, provenance["historical_source_sha256"])

    def test_s010_contract_64_to_192(self):
        source = ROOT / "experiments" / "03_sbohn" / "S-010" / "historical" / "source_from_monograph.py"
        spec = importlib.util.spec_from_file_location("s010_contract_test", source)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        extractor = module.SBOHNFeatureExtractor()
        X = np.zeros((3, 64))
        self.assertEqual(extractor.transform(X).shape, (3, 192))
        self.assertTrue(np.array_equal(extractor.perm_g2[extractor.perm_g], np.arange(64)))

    def test_s004_historical_counter_bug_is_preserved(self):
        source = ROOT / "experiments" / "03_sbohn" / "S-004" / "historical" / "source_from_monograph.py"
        text = source.read_text(encoding="utf-8")
        self.assertEqual(text.count("np.sum(gains > 0)"), 2)
        self.assertIn("worse", text)

    def test_no_nonerror_red_messages_in_stage_scripts(self):
        for name in ["SETUP_STAGE_04.ps1", "RUN_STAGE_04_SMOKE.ps1", "RUN_STAGE_04_FULL.ps1"]:
            path = ROOT / name
            if path.exists():
                self.assertNotIn("ForegroundColor Red", path.read_text(encoding="utf-8"))

    def test_close_numeric_comparison(self):
        actual = "score mean=0.8391\ngain=0.2404\n"
        reported = ROOT / "tests" / "_stage04_reported_tmp.txt"
        reported.write_text("score mean=0.8390\ngain=0.2403\n", encoding="utf-8")
        try:
            result = run_stage_04.compare_text(actual, reported)
        finally:
            reported.unlink()
        self.assertEqual(result["status"], "CLOSE_NUMERIC_MATCH")


if __name__ == "__main__":
    unittest.main()
