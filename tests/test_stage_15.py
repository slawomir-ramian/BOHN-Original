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
BASE = ROOT / "experiments" / "13_rmig_meta_fbohn"
IDS = ["RF-001", "RF-002", "MF-001", "MF-002", "MF-003", "MF-004", "MF-005"]
EXPECTED_HASH = "7c22f9b681a821e5e7be402b3173f909e0c30ffa50ac48ee8f2086af0c33da60"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage15Tests(unittest.TestCase):
    def test_pdf_chronology_ends_with_stage_15(self):
        path = ROOT / "inventory" / "source_chronology.csv"
        path = path if path.exists() else ROOT / "inventory" / "experiments.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 115)
        self.assertEqual([row["id"] for row in rows[108:115]], IDS)

    def test_full_shared_historical_source_and_reported_hashes(self):
        hashes = set()
        for experiment_id in IDS:
            base = BASE / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            source = (base / "historical" / provenance["historical_source_files"][0]).read_text(encoding="utf-8")
            reported = (base / "historical" / provenance["reported_result_file"]).read_text(encoding="utf-8").rstrip("\n")
            source_hash = hashlib.sha256(source.encode()).hexdigest()
            hashes.add(source_hash)
            self.assertEqual(source_hash, provenance["historical_source_sha256"][0])
            self.assertEqual(hashlib.sha256(reported.encode()).hexdigest(), provenance["reported_result_sha256"])
            self.assertEqual(provenance["source_code_level"], "FULL_SUITE")
            self.assertFalse(provenance["historical_code_modified"])
        self.assertEqual(hashes, {EXPECTED_HASH})

    def test_historical_suite_exposes_all_programs(self):
        source = (BASE / "RF-001" / "historical" / "source_from_monograph.py").read_text(encoding="utf-8")
        for program in ["'v1'", "'noise'", "'testA'", "'v2'", "'v3'", "'v4'", "'v5'"]:
            self.assertIn(program, source)
        for function in ["run_v1", "evolve_weighted_meta", "evolve_mixing_v3",
                         "evolve_symbolic_composer", "discover_library_for_dataset"]:
            self.assertIn(f"def {function}", source)

    def test_checkpoint_protocol_is_full(self):
        executor = load(ROOT / "tools" / "execute_historical_stage_15.py", "executor15")
        self.assertEqual(executor.N_SAMPLES, 6000)
        self.assertEqual(executor.N_SEEDS, 10)
        self.assertEqual(executor.NOISES, [0.0, 0.1, 0.3, 0.5])
        source = (ROOT / "tools" / "execute_historical_stage_15.py").read_text(encoding="utf-8")
        self.assertIn("pop=80, generations=30, elite=8", source)
        self.assertIn("runs=12, library_size=32", source)

    def test_rmig_and_feature_contracts(self):
        from bohn_original.rmig_meta_fbohn import (OPS, check_z3_equivariance, fbohn_features,
                                                   fbohn_poly_control_features, generate_signals,
                                                   symbolic_op, z3_permutation)
        signals = generate_signals(24, seed=15)
        features = fbohn_features(signals)
        self.assertEqual(features.shape, (24, 30))
        self.assertEqual(fbohn_poly_control_features(signals).shape, (24, 84))
        self.assertTrue(check_z3_equivariance())
        self.assertTrue(np.allclose(features, fbohn_features(signals[:, z3_permutation(1)])))
        for operator in OPS:
            self.assertTrue(np.isfinite(symbolic_op(features[:, 0], features[:, 1], operator)).all())

    def test_runner_reference_classification(self):
        runner = load(ROOT / "tools" / "run_stage_15.py", "runner15")
        v1 = {"summary": [{"representation": name, "acc_mean": value, "acc_std": 0, "feature_dim": 1}
                          for name, value in runner.REFERENCE_V1.items()]}
        self.assertEqual(runner.compare_v1(v1)["status"], "CLOSE_NUMERIC_MATCH")
        test_a = {"summary": [{"noise": noise, "representation": name, "acc_mean": value,
                               "acc_std": 0, "feature_dim": 1}
                              for noise, row in runner.REFERENCE_TEST_A.items() for name, value in row.items()]}
        self.assertEqual(runner.compare_test_a(test_a)["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ["SETUP_STAGE_15.ps1", "RUN_STAGE_15_SMOKE.ps1", "RUN_STAGE_15_FULL.ps1"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
