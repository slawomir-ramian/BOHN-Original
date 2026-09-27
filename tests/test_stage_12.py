import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "10_sota_and_scaling"
IDS = ["SOTA-001", "SOTA-002"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage12Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        chronology = ROOT / "inventory" / "source_chronology.csv"
        source = chronology if chronology.exists() else ROOT / "inventory" / "experiments.csv"
        with source.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[87:89]], IDS)
        if chronology.exists():
            self.assertEqual([int(row["source_order"]) for row in rows[87:89]], [88, 89])

    def test_historical_and_reported_hashes(self):
        for experiment_id in IDS:
            base = BASE / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            source = (base / "historical" / "source_from_monograph.py").read_text(encoding="utf-8").rstrip("\n")
            result = (base / "historical" / provenance["reported_result_file"]).read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), provenance["historical_source_sha256"][0])
            self.assertEqual(hashlib.sha256(result.encode()).hexdigest(), provenance["reported_result_sha256"])
            self.assertFalse(provenance["historical_code_modified"])

    def test_source_boundary_is_full_and_compatibility_is_separate(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["source_code_level"], "FULL_SOURCE")
            self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE_WITH_PATH_COMPATIBILITY")
            self.assertEqual(provenance["compatibility_changes"], ["redirect_absolute_tmp_paths_in_runtime_copy_only"])

    def test_published_protocol_is_preserved(self):
        accuracy = (BASE / "SOTA-001" / "historical" / "source_from_monograph.py").read_text(encoding="utf-8")
        scaling = (BASE / "SOTA-002" / "historical" / "source_from_monograph.py").read_text(encoding="utf-8")
        self.assertIn("range(2000)", accuracy)
        self.assertIn("range(500)", accuracy)
        self.assertIn("for ep in range(3)", accuracy)
        self.assertNotIn("manual_seed", accuracy)
        self.assertIn("resolutions = [28, 56, 112, 224, 448]", scaling)
        self.assertIn("for _ in range(3):", scaling)
        self.assertIn("time.time()", scaling)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "PyTorch is installed during SETUP_STAGE_12")
    def test_exact_architecture_contracts(self):
        from bohn_original.sota_scaling import CNN, FractalSBOHN, MLP, ViT, parameter_count
        self.assertEqual(parameter_count(FractalSBOHN(28, 1, 10, 16, 4)), 54298)
        self.assertEqual(parameter_count(CNN(1, 10)), 23946)
        self.assertEqual(parameter_count(ViT(28, 1, 10, 64, 4, 2)), 71946)
        self.assertEqual(parameter_count(MLP(784, 10)), 235146)
        expected_sbohn = [54298, 63706, 101338, 251866, 853978]
        expected_vit = [71946, 81354, 118986, 269514, 871626]
        for resolution, sbohn, vit in zip([28, 56, 112, 224, 448], expected_sbohn, expected_vit):
            self.assertEqual(parameter_count(FractalSBOHN(resolution, 1, 10, 16, 4)), sbohn)
            self.assertEqual(parameter_count(ViT(resolution, 1, 10, 64, 4, 2)), vit)

    def test_runner_classifies_reference_shapes(self):
        runner = load_module(ROOT / "tools" / "run_stage_12.py", "stage12_runner")
        first = {
            name: {"acc": accuracy, "params": runner.PUBLISHED_PARAMS_28[name], "mem_mb": 0.0, "train_s": 0.0}
            for name, accuracy in runner.PUBLISHED_ACCURACY.items()
        }
        second = {
            name: {
                "times": dict(runner.PUBLISHED_TIMES[name]), "params": dict(runner.PUBLISHED_PARAMS[name]),
                "mem": {}, "patches": {}, "scaling_exp": runner.PUBLISHED_SCALING[name], "est_4k_ms": 0.0,
            }
            for name in runner.PUBLISHED_PARAMS
        }
        self.assertEqual(runner.comparison("SOTA-001", first)["status"], "CLOSE_NUMERIC_MATCH")
        self.assertEqual(runner.comparison("SOTA-002", second)["status"], "CLOSE_NUMERIC_MATCH")

    def test_hardware_dependent_metrics_are_explicit(self):
        first = json.loads((BASE / "SOTA-001" / "provenance.json").read_text(encoding="utf-8"))
        second = json.loads((BASE / "SOTA-002" / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(first["hardware_dependent_metrics"], ["train_s"])
        self.assertEqual(second["hardware_dependent_metrics"], ["times", "scaling_exp", "est_4k_ms"])

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_12.ps1", "RUN_STAGE_12_SMOKE.ps1", "RUN_STAGE_12_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
