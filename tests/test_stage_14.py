import ast
import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "12_moe_evolution"
IDS = ["MOE-001", "MOE-009", "MOE-002", "MOE-003", "MOE-004", "MOE-005", "MOE-006", "MOE-007", "MOE-008"]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage14Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        path = ROOT / "inventory" / "source_chronology.csv"
        path = path if path.exists() else ROOT / "inventory" / "experiments.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[99:108]], IDS)

    def test_historical_and_reported_hashes(self):
        for experiment_id in IDS:
            base = BASE / experiment_id
            provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
            source_name = provenance["historical_source_files"][0]
            source = (base / "historical" / source_name).read_text(encoding="utf-8").rstrip("\n")
            reported = (base / "historical" / provenance["reported_result_file"]).read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), provenance["historical_source_sha256"][0])
            self.assertEqual(hashlib.sha256(reported.encode()).hexdigest(), provenance["reported_result_sha256"])
            self.assertFalse(provenance["historical_code_modified"])

    def test_source_boundaries_are_explicit(self):
        expected = {
            "MOE-001": "SOURCE_FRAGMENT_ONLY", "MOE-009": "SOURCE_FRAGMENT_ONLY",
            "MOE-002": "SOURCE_FRAGMENT_ONLY", "MOE-003": "SOURCE_FRAGMENT_ONLY",
            "MOE-004": "FULL", "MOE-005": "SHARED_LISTING_TARGET_CODE_ABSENT",
            "MOE-006": "FULL_SHARED_LISTING", "MOE-007": "SHARED_LISTING_TARGET_CODE_ABSENT",
            "MOE-008": "FULL",
        }
        for experiment_id, level in expected.items():
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["source_code_level"], level)
            self.assertEqual(provenance["listing_target_code_present"], experiment_id in {"MOE-004", "MOE-006", "MOE-008"})

    def test_published_placeholders_are_not_presented_as_runs(self):
        first = (BASE / "MOE-001" / "historical" / "source_fragment_from_monograph.py").read_text(encoding="utf-8")
        sparse = (BASE / "MOE-002" / "historical" / "source_fragment_from_monograph.py").read_text(encoding="utf-8")
        shared = (BASE / "MOE-005" / "historical" / "shared_listing_context_from_monograph.py").read_text(encoding="utf-8")
        self.assertNotIn("# --- Full Pipeline ---", first)
        self.assertNotIn("SparseMoESystem(", sparse.split("class SparseMoESystem", 1)[-1])
        self.assertIn("# ... (train MNIST, then Fashion, measure MNIST retention)", shared)
        self.assertNotIn("SharedSpecificMoE(", shared.split("class SharedSpecificMoE", 1)[-1])

    @unittest.skipUnless(importlib.util.find_spec("torch"), "PyTorch is installed by setup")
    def test_architecture_contracts(self):
        import torch
        from bohn_original.moe_evolution import ConfidenceRoutedMoE, HardAssignMoE, HybridBNLNMoE, SharedBaseBN, ExpertTopLN
        x = torch.randn(3, 1, 28, 28)
        hard = HardAssignMoE()
        self.assertEqual(tuple(hard.forward_hard(x, 0).shape), (3, 10))
        confidence = ConfidenceRoutedMoE()
        self.assertEqual(tuple(confidence.forward_confidence(x)[0].shape), (3, 10))
        hybrid = HybridBNLNMoE()
        self.assertIsInstance(hybrid.base, SharedBaseBN)
        self.assertTrue(all(isinstance(expert, ExpertTopLN) for expert in hybrid.experts))
        self.assertEqual(tuple(hybrid.forward_gated(x)[0].shape), (3, 10))

    def test_runner_parsers_and_reference_classification(self):
        runner = load(ROOT / "tools" / "run_stage_14.py", "runner14")
        hard_text = "\n".join(
            f"  {domain}: {runner.PUB_HARD_ACC[domain]:.1f}% | Gate: {[f'E{i}:{value:.1f}%' for i, value in enumerate(runner.PUB_HARD_ROUTE[domain])]}"
            for domain in runner.DOMAINS)
        hard = runner.parse_hard_assign(hard_text)
        self.assertEqual(runner.compare_hard(hard)["status"], "CLOSE_NUMERIC_MATCH")
        confidence_lines = ["Oracle (hard assignment):"]
        confidence_lines += [f"    {domain}: 90.0%" for domain in runner.DOMAINS]
        for method, values in runner.PUB_CONFIDENCE.items():
            confidence_lines.append(f"  {method} routing:")
            confidence_lines += [f"    {domain}: {values[domain]:.1f}% | Routing: [E0:34.0%, E1:33.0%, E2:33.0%]" for domain in runner.DOMAINS]
        confidence = runner.parse_confidence("\n".join(confidence_lines))
        self.assertEqual(runner.compare_confidence(confidence)["status"], "CLOSE_NUMERIC_MATCH")
        hybrid_lines = []
        for domain, (gated, oracle, gate) in runner.PUB_HYBRID.items():
            hybrid_lines.append(f"  {domain}: Gated={gated:.1f}%, Oracle={oracle:.1f}%, Gate=[" + ", ".join(f"E{i}:{v:.1f}%" for i, v in enumerate(gate)) + "]")
        hybrid_lines += ["  Avg Gated: 90.5%", "  Avg Oracle: 90.5%", "  Forgetting: 0.0%", "  Gate Overhead: 0.0%"]
        hybrid = runner.parse_hybrid("\n".join(hybrid_lines))
        self.assertEqual(runner.compare_hybrid(hybrid)["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ["SETUP_STAGE_14.ps1", "RUN_STAGE_14_SMOKE.ps1", "RUN_STAGE_14_FULL.ps1"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
