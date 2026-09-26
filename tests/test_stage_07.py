import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "05_permutation_and_representation"
IDS = ["PL-001", "PL-002", "PL-003", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001", "HD-002", "HD-003", "CMP-001", "CMP-002"]
FULL = {"PL-001", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001", "HD-002"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage07Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[33:45]], IDS)
        self.assertEqual([int(row["source_order"]) for row in rows[33:45]], list(range(34, 46)))

    def test_full_and_narrative_boundaries_are_explicit(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            if experiment_id in FULL:
                self.assertEqual(provenance["source_code_level"], "FULL_UNCAPTIONED")
                self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE")
                self.assertTrue(provenance["historical_source_files"])
            else:
                self.assertEqual(provenance["source_code_level"], "NARRATIVE_ONLY")
                self.assertEqual(provenance["execution_mode"], "AUDITED_REPORTED_RESULT")
                self.assertEqual(provenance["historical_source_files"], [])
                self.assertFalse((BASE / experiment_id / "reconstruction").exists())

    def test_historical_and_reported_hashes(self):
        for experiment_id in IDS:
            base = BASE / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            for filename, expected in zip(provenance["historical_source_files"], provenance["historical_source_sha256"]):
                text = (base / "historical" / filename).read_text(encoding="utf-8").rstrip("\n")
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected)
            result = (base / "historical" / provenance["reported_result_file"]).read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(hashlib.sha256(result.encode()).hexdigest(), provenance["reported_result_sha256"])
            self.assertFalse(provenance["historical_code_modified"])

    def test_high_dimension_units_share_exact_published_listings(self):
        a = json.loads((BASE / "HD-001" / "provenance.json").read_text(encoding="utf-8"))
        b = json.loads((BASE / "HD-002" / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(a["listing_indices"], [51, 52])
        self.assertEqual(a["historical_source_sha256"], b["historical_source_sha256"])

    def test_permutation_and_z3_primitives(self):
        from bohn_original.permutation_representation import flip_horizontal, rotate_180, z3_features, z3_permutation

        x = np.arange(5 * 64).reshape(5, 64)
        np.testing.assert_array_equal(rotate_180(rotate_180(x)), x)
        np.testing.assert_array_equal(flip_horizontal(flip_horizontal(x)), x)
        perm = z3_permutation(63)
        np.testing.assert_array_equal(perm[perm[perm]], np.arange(63))
        self.assertEqual(z3_features(np.ones((4, 63)), perm).shape, (4, 189))

    def test_linear_cka_self_similarity(self):
        from bohn_original.permutation_representation import linear_cka

        rng = np.random.default_rng(7)
        values = rng.normal(size=(30, 12))
        self.assertAlmostEqual(linear_cka(values, values), 1.0, places=10)

    def test_runner_classifies_core_conclusions(self):
        runner = load_module(ROOT / "tools" / "run_stage_07.py", "stage07_runner")
        pl = runner.comparison("PL-001", "Baseline x accuracy: 0.8204\nRandom mean accuracy: 0.8398\nBest evolved accuracy: 0.9481\n")
        self.assertEqual(pl["status"], "CLOSE_NUMERIC_MATCH")
        ar4 = runner.comparison("AR-004", "Mean pairwise perm similarity: 0.0319\nMean pairwise CKA: 0.7965\n")
        self.assertTrue(ar4["scientific_conclusion_preserved"])
        hd2 = runner.comparison("HD-002", "n=  2000  base=0.51  sbohn=0.57  gain=0.06  wins=10/10\nn=  5000  base=0.51  sbohn=0.63  gain=0.12  wins=10/10\nn= 10000  base=0.51  sbohn=0.69  gain=0.18  wins=10/10\n")
        self.assertEqual(hd2["status"], "CONCLUSION_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_07.ps1", "RUN_STAGE_07_SMOKE.ps1", "RUN_STAGE_07_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
