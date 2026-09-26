import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "07_fractal_patch"
IDS = [
    "FR-001", "FR-004", "FR-002", "FR-003",
    "PT-001", "PT-002", "PT-003", "PT-004", "PT-005",
    "HR-001", "HR-002", "HR-003", "HR-004", "HR-005", "HR-006", "HR-007",
]
EXECUTABLE = {"FR-002", "FR-003", "PT-001", "PT-002", "PT-004", "PT-005"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage09Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[56:72]], IDS)
        self.assertEqual([int(row["source_order"]) for row in rows[56:72]], list(range(57, 73)))
        self.assertEqual(IDS[:4], ["FR-001", "FR-004", "FR-002", "FR-003"])

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

    def test_source_boundaries_are_explicit(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            if experiment_id in EXECUTABLE:
                self.assertTrue(provenance["listing_target_code_present"])
                self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE")
                self.assertEqual(provenance["source_code_level"], "FULL_IN_CHAPTER")
            else:
                self.assertFalse(provenance["listing_target_code_present"])
                self.assertEqual(provenance["execution_mode"], "AUDITED_REPORTED_RESULT")

    def test_shared_program_hashes(self):
        fractal = {
            json.loads((BASE / item / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for item in ("FR-002", "FR-003")
        }
        patch = {
            json.loads((BASE / item / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for item in ("PT-001", "PT-002", "PT-003", "PT-004", "PT-005")
        }
        self.assertEqual(len(fractal), 1)
        self.assertEqual(len(patch), 1)

    def test_fractal_and_patch_primitives(self):
        from bohn_original.fractal_patch import doubly_stochastic_error, extract_patches, log_sinkhorn, multiscale_features, permute_patch_sequence

        torch.manual_seed(9)
        images = torch.randn(3, 1, 32, 32)
        levels = multiscale_features(images, 4)
        self.assertEqual([value.shape[1] for value in levels], [16, 64, 256, 1024])
        patches = extract_patches(images, 8)
        self.assertEqual(tuple(patches.shape), (3, 16, 64))
        matrix = log_sinkhorn(torch.randn(3, 16, 16), n_iter=30, tau=0.3)
        self.assertLess(doubly_stochastic_error(matrix), 0.02)
        self.assertEqual(tuple(permute_patch_sequence(patches, matrix).shape), (3, 16, 64))

    def test_compatibility_wrapper_preserves_source(self):
        wrapper = load_module(ROOT / "tools" / "execute_historical_stage_09.py", "stage09_executor")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "sample.py"
            source.write_text("import os\nos.makedirs('/tmp/mnist_data', exist_ok=True)\nwith open('/tmp/real_results.json','w') as f: f.write('{}')\n", encoding="utf-8")
            before = source.read_bytes()
            old_argv = sys.argv
            try:
                sys.argv = ["execute_historical_stage_09.py", str(source), "--run-dir", str(base / "run"), "--cache-dir", str(base / "cache")]
                self.assertEqual(wrapper.main(), 0)
            finally:
                sys.argv = old_argv
            self.assertTrue((base / "cache" / "mnist_data").is_dir())
            self.assertEqual((base / "run" / "real_results.json").read_text(encoding="utf-8"), "{}")
            self.assertEqual(source.read_bytes(), before)

    def test_runner_classifies_reference_shapes(self):
        runner = load_module(ROOT / "tools" / "run_stage_09.py", "stage09_runner")
        fractal = {
            "m_F2L": {"acc": 0.7675}, "m_F3L": {"acc": 0.8825}, "m_F4L": {"acc": 0.895},
            "m_F4L_h64": {"acc": 0.9}, "m_MLP128": {"acc": 0.9075},
        }
        self.assertEqual(runner.comparison("FR-002", fractal)["status"], "CLOSE_NUMERIC_MATCH")
        rows = [{"acc": value} for value in (0.916, 0.912, 0.798, 0.864, 0.916, 0.908, 0.916, 0.918, 0.914)]
        self.assertEqual(runner.comparison("PT-001", {"mnist": rows})["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_09.ps1", "RUN_STAGE_09_SMOKE.ps1", "RUN_STAGE_09_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
