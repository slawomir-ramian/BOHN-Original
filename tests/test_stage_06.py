import csv
import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "04_symmetry_discovery"
IDS = ["SD-001", "SD-002", "SD-003", "SD-004", "ASD-001"]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage06Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([r["id"] for r in rows[28:33]], IDS)
        self.assertEqual([int(r["source_order"]) for r in rows[28:33]], list(range(29, 34)))

    def test_historical_hashes_and_reported_hashes(self):
        for experiment_id in IDS:
            base = BASE / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            source = (base / "historical" / "source_from_monograph.py").read_text(
                encoding="utf-8"
            ).rstrip("\n")
            self.assertEqual(
                hashlib.sha256(source.encode()).hexdigest(),
                provenance["historical_source_sha256"],
            )
            result = base / "historical" / provenance["reported_result_file"]
            text = result.read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(
                hashlib.sha256(text.encode()).hexdigest(),
                provenance["reported_result_sha256"],
            )

    def test_all_units_preserve_full_historical_source(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text())
            self.assertEqual(provenance["source_code_level"], "FULL_UNCAPTIONED")
            self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE")
            self.assertFalse(provenance["historical_code_modified"])
        self.assertFalse((BASE / "SD-001" / "reconstruction").exists())
        self.assertTrue((BASE / "ASD-001" / "reconstruction").exists())

    def test_transforms_are_involutions(self):
        from bohn_original.symmetry_discovery import flip_horizontal, rotate_180

        values = np.arange(3 * 64).reshape(3, 64)
        np.testing.assert_array_equal(flip_horizontal(flip_horizontal(values)), values)
        np.testing.assert_array_equal(rotate_180(rotate_180(values)), values)

    def test_feature_dimensions(self):
        from bohn_original.symmetry_discovery import asymmetry, sum_asymmetry

        x = np.arange(4 * 64).reshape(4, 64)
        y = x[:, ::-1]
        self.assertEqual(asymmetry(x, y).shape, (4, 64))
        self.assertEqual(sum_asymmetry(x, y).shape, (4, 128))

    def test_asd_historical_contract_is_documented(self):
        source = (BASE / "ASD-001" / "historical" / "source_from_monograph.py").read_text()
        make_labels = source[source.index("def make_labels"):source.index("digits =")]
        self.assertIn("rotate_180", make_labels)
        self.assertNotIn("flip_horizontal", make_labels)
        classifier = re.search(r"LogisticRegression\((.*?)\)", source, re.S)
        self.assertIsNotNone(classifier)
        self.assertNotIn("random_state", classifier.group(1))

    def test_asd_report_parser_accepts_reference_shape(self):
        runner = load_module(ROOT / "tools" / "run_stage_06.py", "stage06_runner")
        chunks = []
        accuracies = [0.9244, 0.9554, 0.9630, 0.9630]
        for c, accuracy in zip([0.02, 0.05, 0.10, 0.20], accuracies):
            chunks.append(
                f"=== C = {c:.2f} ===\nAccuracy: {accuracy:.4f}\n"
                "Top1 True: 10/10\nBoth True Top10: 10/10\n"
                "Mean Best Rank: 1.0\nMean Worst Rank: 2.0\n"
            )
        result = runner.compare_asd("\n".join(chunks))
        self.assertTrue(result["scientific_conclusion_preserved"])
        self.assertEqual(result["status"], "CLOSE_NUMERIC_MATCH")

    def test_recovery_classifies_primary_match_separately(self):
        recovery = load_module(
            ROOT / "tools" / "run_asd_001_recovery.py", "stage06_recovery"
        )
        rows = {
            key: {
                "accuracy": accuracy,
                "top1_true": 10,
                "both_true_top10": 0,
                "mean_best_rank": 1.0,
                "mean_worst_rank": 50.0,
            }
            for key, accuracy in recovery.EXPECTED_ACCURACY.items()
        }
        result = recovery.comparison(rows)
        self.assertTrue(result["primary_encoded_symmetry_reproduced"])
        self.assertFalse(result["secondary_reported_symmetry_reproduced"])
        self.assertEqual(
            result["status"], "PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH"
        )

    def test_red_is_reserved_for_real_errors(self):
        for name in ["SETUP_STAGE_06.ps1", "RUN_STAGE_06_SMOKE.ps1", "RUN_STAGE_06_FULL.ps1", "RUN_STAGE_06_ASD_RECOVERY.ps1"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)

    def test_recovery_keeps_historical_contract(self):
        recovery = (ROOT / "tools" / "run_asd_001_recovery.py").read_text(encoding="utf-8")
        self.assertIn('c_values = [0.10] if args.quick else [0.02, 0.05, 0.10, 0.20]', recovery)
        self.assertIn('random_count = 5 if args.quick else 97', recovery)
        self.assertIn('max_iter = 500 if args.quick else 5000', recovery)
        self.assertIn('solver="saga"', recovery)
        self.assertIn('penalty="l1"', recovery)
        self.assertIn('default=2', recovery)


if __name__ == "__main__":
    unittest.main()
