import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "09_adaptation_and_continual"
IDS = ["AD-001", "AD-002", "AD-003", "CL-001", "CL-002"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage11Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[82:87]], IDS)
        self.assertEqual([int(row["source_order"]) for row in rows[82:87]], list(range(83, 88)))

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

    def test_partial_source_boundary_is_explicit(self):
        hashes = {}
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["source_code_level"], "SOURCE_FRAGMENT_ONLY")
            self.assertEqual(provenance["execution_mode"], "RECONSTRUCTION_FROM_PUBLISHED_FRAGMENT")
            self.assertFalse(provenance["listing_target_code_present"])
            self.assertFalse(provenance["reconstruction_is_historical_source"])
            hashes[experiment_id] = provenance["historical_source_sha256"][0]
        self.assertEqual(hashes["AD-001"], hashes["CL-001"])
        self.assertEqual(hashes["AD-002"], hashes["AD-003"])
        self.assertEqual(hashes["AD-002"], hashes["CL-002"])
        self.assertNotEqual(hashes["AD-001"], hashes["AD-002"])

    def test_published_fragments_really_omit_target_phases(self):
        listing58 = (BASE / "AD-001" / "historical" / "source_fragment_from_monograph.py").read_text(encoding="utf-8")
        listing59 = (BASE / "AD-002" / "historical" / "source_fragment_from_monograph.py").read_text(encoding="utf-8")
        self.assertIn("PHASE 2: Few-shot adaptation", listing58)
        self.assertIn("see full code", listing58)
        self.assertIn("# For each n_shots", listing59)
        self.assertIn("# === PHASE 3: Continual Learning ===", listing59)

    def test_exact_parameter_contracts(self):
        from bohn_original.adaptation_continual import (
            FewShotSBOHN, PermHeadSBOHN, parameter_count, parameter_count_of
        )
        small = PermHeadSBOHN()
        large = FewShotSBOHN()
        self.assertEqual(parameter_count(small), 46106)
        self.assertEqual(parameter_count_of(small.adaptation_params()), 714)
        self.assertEqual(parameter_count_of(small.perm_only_params()), 64)
        self.assertEqual(parameter_count_of(small.head_only_params()), 650)
        self.assertEqual(parameter_count(large), 170522)
        self.assertEqual(parameter_count_of(large.perm_only_params()), 1024)
        self.assertEqual(parameter_count_of(large.head_only_params()), 165258)

    def test_task_swap_is_exact(self):
        from bohn_original.adaptation_continual import FewShotSBOHN, PermHeadSBOHN
        torch.manual_seed(42)
        small = PermHeadSBOHN()
        task = small.save_task_params()
        with torch.no_grad():
            for parameter in small.adaptation_params():
                parameter.add_(1.0)
        small.load_task_params(task)
        restored = small.save_task_params()
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(task["perm"], restored["perm"])))
        self.assertTrue(torch.equal(task["head_w"], restored["head_w"]))
        self.assertTrue(torch.equal(task["head_b"], restored["head_b"]))
        large = FewShotSBOHN()
        permutations = large.save_permutations()
        with torch.no_grad():
            for parameter in large.perm_only_params():
                parameter.mul_(0.0)
        large.load_permutations(permutations)
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(permutations, large.save_permutations())))

    def test_runner_classifies_exact_reference_shapes(self):
        runner = load_module(ROOT / "tools" / "run_stage_11.py", "stage11_runner")
        first = {
            "fewshot": {shots: dict(zip(runner.AD1_KEYS, values)) for shots, values in runner.PUBLISHED_AD1.items()},
            "continual": {
                "sbohn_mnist_before": 69.60, "sbohn_fashion": 58.50,
                "sbohn_mnist_after_restore": 69.60, "sbohn_mnist_degradation": 0.0,
                "mlp_mnist_before": 92.10, "mlp_fashion": 83.20,
                "mlp_mnist_after_fashion": 21.20, "mlp_mnist_degradation": 70.90,
            },
        }
        second = {
            "fewshot": {shots: dict(zip(runner.AD2_KEYS, values)) for shots, values in runner.PUBLISHED_AD2.items()},
            "continual": {
                "sbohn_mnist_before": 89.52, "sbohn_fashion_perm_only": 29.07,
                "sbohn_mnist_after_restore": 89.52, "sbohn_mnist_degradation": 0.0,
                "mlp_mnist_before": 89.99, "mlp_fashion": 72.19,
                "mlp_mnist_after_fashion": 65.85, "mlp_mnist_degradation": 24.14,
            },
        }
        self.assertEqual(runner.comparison("AD-001", first)["status"], "CLOSE_NUMERIC_MATCH")
        self.assertEqual(runner.comparison("CL-001", first)["status"], "CLOSE_NUMERIC_MATCH")
        self.assertEqual(runner.comparison("AD-002", second)["status"], "CLOSE_NUMERIC_MATCH")
        self.assertEqual(runner.comparison("AD-003", second)["status"], "CLOSE_NUMERIC_MATCH")
        self.assertEqual(runner.comparison("CL-002", second)["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_11.ps1", "RUN_STAGE_11_SMOKE.ps1", "RUN_STAGE_11_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
