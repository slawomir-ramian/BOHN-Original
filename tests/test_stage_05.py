from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from bohn_original.so2 import analytical_profile, asymmetry_profile, moment_features, rotate_blocks
import run_stage_05


EXPECTED = [
    "G-001", "SO-001", "SO-002", "SO-003",
    "SO-004", "SO-005", "SO-006", "SO-007",
]


class Stage05Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        self.assertEqual(run_stage_05.SOURCE_CHRONOLOGY, EXPECTED)
        with (ROOT / "inventory" / "source_chronology.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if 21 <= int(row["source_order"]) <= 28]
        self.assertEqual([row["id"] for row in selected], EXPECTED)

    def test_historical_hashes_and_reported_hashes(self):
        for experiment_id in EXPECTED:
            base = ROOT / "experiments" / "04_generalization_so2" / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            source_name = provenance["source_filename"]
            if source_name:
                source = (base / "historical" / source_name).read_text(encoding="utf-8")
                self.assertEqual(
                    hashlib.sha256(source[:-1].encode("utf-8")).hexdigest(),
                    provenance["historical_source_sha256"],
                )
            reported = (base / "historical" / "reported_results.txt").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                hashlib.sha256(reported[:-1].encode("utf-8")).hexdigest(),
                provenance["reported_result_sha256"],
            )

    def test_partial_sources_are_not_presented_as_full(self):
        so002 = ROOT / "experiments" / "04_generalization_so2" / "SO-002"
        self.assertFalse((so002 / "historical" / "source_from_monograph.py").exists())
        self.assertTrue((so002 / "reconstruction" / "reproduce.py").exists())
        so005 = ROOT / "experiments" / "04_generalization_so2" / "SO-005"
        self.assertTrue(
            (so005 / "historical" / "source_fragment_from_monograph.py").exists()
        )
        self.assertFalse((so005 / "historical" / "source_from_monograph.py").exists())

    def test_profile_matches_analytical_formula(self):
        x = np.array([3.0, 4.0])
        thetas = np.linspace(0.0, 2.0 * np.pi, 37)
        self.assertTrue(
            np.allclose(
                asymmetry_profile(x, thetas),
                analytical_profile(5.0, thetas),
                atol=1e-12,
                rtol=0.0,
            )
        )

    def test_moment_representation_is_rotation_invariant(self):
        X = np.random.default_rng(42).normal(size=(8, 8))
        phi = moment_features(X)
        rotated = moment_features(rotate_blocks(X, 0.731))
        self.assertTrue(np.allclose(phi, rotated, atol=1e-10, rtol=0.0))

    def test_close_numeric_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            reported = Path(directory) / "reported.txt"
            reported.write_text("score=0.8039\nerror=1.14e-13\n", encoding="utf-8")
            result = run_stage_05.compare_text(
                "score=0.8040\nerror=1.20e-13\n", reported
            )
        self.assertEqual(result["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in [
            "SETUP_STAGE_05.ps1",
            "RUN_STAGE_05_SMOKE.ps1",
            "RUN_STAGE_05_FULL.ps1",
        ]:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)


if __name__ == "__main__":
    unittest.main()
