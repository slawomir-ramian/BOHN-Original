import builtins
import csv
import hashlib
import importlib.util
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "06_learnable_sinkhorn"
IDS = ["LS-001", "LS-002", "LS-003", "LS-004", "LS-005", "LS-006", "LD-001", "LD-002", "LD-003", "LD-004", "LD-005"]
AUDITED_ONLY = {"LS-002", "LS-003", "LS-004", "LS-005", "LS-006"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage08Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[45:56]], IDS)
        self.assertEqual([int(row["source_order"]) for row in rows[45:56]], list(range(46, 57)))

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

    def test_shared_listing_boundary_is_explicit(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            if experiment_id in AUDITED_ONLY:
                self.assertFalse(provenance["listing_target_code_present"])
                self.assertEqual(provenance["source_code_level"], "SHARED_LISTING_TARGET_CODE_ABSENT")
                self.assertEqual(provenance["execution_mode"], "AUDITED_REPORTED_RESULT")
            else:
                self.assertTrue(provenance["listing_target_code_present"])
                self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE")

    def test_shared_listing_hashes(self):
        ls_hashes = {
            json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for experiment_id in IDS[:6]
        }
        abc_hashes = {
            json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for experiment_id in IDS[6:9]
        }
        de_hashes = {
            json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for experiment_id in IDS[9:]
        }
        self.assertEqual(len(ls_hashes), 1)
        self.assertEqual(len(abc_hashes), 1)
        self.assertEqual(len(de_hashes), 1)

    def test_sinkhorn_primitives(self):
        from bohn_original.learnable_sinkhorn import doubly_stochastic_error, log_sinkhorn, naive_sinkhorn, row_entropy

        torch.manual_seed(7)
        scores = torch.randn(12, 12)
        naive = naive_sinkhorn(scores, n_iters=30, tau=0.5)
        stable = log_sinkhorn(scores, n_iters=30, tau=0.5)
        self.assertTrue(torch.isfinite(naive).all())
        self.assertTrue(torch.isfinite(stable).all())
        self.assertLess(doubly_stochastic_error(naive), 1e-4)
        self.assertLess(doubly_stochastic_error(stable), 1e-4)
        self.assertGreater(float(row_entropy(stable)), 0.0)

    def test_historical_tmp_redirector_preserves_source(self):
        wrapper = load_module(ROOT / "tools" / "execute_historical_stage_08.py", "stage08_executor")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "sample.py"
            source.write_text("with open('/tmp/probe.json', 'w') as f:\n    f.write('ok')\n", encoding="utf-8")
            before = source.read_bytes()
            destination = base / "redirected"
            old_argv = sys.argv
            try:
                sys.argv = ["execute_historical_stage_08.py", str(source), "--tmp-dir", str(destination)]
                self.assertEqual(wrapper.main(), 0)
            finally:
                sys.argv = old_argv
            self.assertEqual((destination / "probe.json").read_text(encoding="utf-8"), "ok")
            self.assertEqual(source.read_bytes(), before)

    def test_runner_classifies_reference_shapes(self):
        runner = load_module(ROOT / "tools" / "run_stage_08.py", "stage08_runner")
        text = (
            "SBOHN-v1 tau=1.0           A(flip)     0.8320     80   1.00s\n"
            "SBOHN-v1 tau-cos           A(flip)     0.8740     80   1.00s\n"
            "SBOHN-InpDep               A(flip)     0.8780     80   1.00s\n"
            "MLP-B                      B(blind)    0.7190    120   1.00s\n"
            "SBOHN-InpDep-B             B(blind)    0.7220    120   1.00s\n"
        )
        result = runner.comparison("LS-001", text, {})
        self.assertEqual(result["status"], "CLOSE_NUMERIC_MATCH")
        ld1 = {"test_a": {"0.001": {"naive_ok": True, "log_ok": True, "naive_ds": 0.3447, "log_ds": 0.3001}}}
        self.assertEqual(runner.comparison("LD-001", "", ld1)["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_08.ps1", "RUN_STAGE_08_SMOKE.ps1", "RUN_STAGE_08_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
