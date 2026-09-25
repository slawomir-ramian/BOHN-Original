import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "04_symmetry_discovery" / "ASD-001"
PROTOCOL = BASE / "reconstruction" / "two_symmetry_protocol.py"
LOCK = BASE / "reconstruction" / "ASD-001R_PROTOCOL_LOCK.json"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ASD001RTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_module(PROTOCOL, "asd001r_protocol_tests")

    def test_historical_source_is_unchanged(self):
        provenance = json.loads((BASE / "provenance.json").read_text(encoding="utf-8"))
        source = (BASE / "historical" / "source_from_monograph.py").read_text(
            encoding="utf-8"
        ).rstrip("\n")
        self.assertEqual(
            hashlib.sha256(source.encode()).hexdigest(),
            provenance["historical_source_sha256"],
        )

    def test_both_symmetries_contribute_to_labels(self):
        values = np.random.default_rng(7).normal(size=(40, 64))
        _, flip_signal, rotate_signal, telemetry = (
            self.protocol.make_two_symmetry_labels(values)
        )
        self.assertAlmostEqual(float(flip_signal.std()), 1.0)
        self.assertAlmostEqual(float(rotate_signal.std()), 1.0)
        self.assertAlmostEqual(telemetry["flip_signal_std"], 1.0)
        self.assertAlmostEqual(telemetry["rotate_signal_std"], 1.0)

    def test_candidate_order_is_shuffled_and_reproducible(self):
        blocks = {"flip_horizontal": None, "rotate_180": None}
        blocks.update({f"rand_{index:02d}": None for index in range(20)})
        first, seed_a = self.protocol.shuffled_names(blocks, 100, 0.10)
        second, seed_b = self.protocol.shuffled_names(blocks, 100, 0.10)
        self.assertEqual(first, second)
        self.assertEqual(seed_a, seed_b)
        self.assertNotEqual(first, sorted(blocks))

    def test_zero_importance_is_unresolved(self):
        names = ["rand_00", "flip_horizontal", "rotate_180"]
        importance = {"rand_00": 0.0, "flip_horizontal": 2.0, "rotate_180": 1.0}
        ranking, ranks, unresolved = self.protocol.strict_ranking(importance, names)
        self.assertEqual(ranking, ["flip_horizontal", "rotate_180"])
        self.assertEqual(ranks["flip_horizontal"], 1)
        self.assertEqual(ranks["rotate_180"], 2)
        self.assertIsNone(ranks["rand_00"])
        self.assertEqual(unresolved, ["rand_00"])

    def test_pilot_configuration_is_separate_from_historical_seeds(self):
        runner_text = (ROOT / "tools" / "run_asd_001r_pilot.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("seeds = [100, 101, 102]", runner_text)
        self.assertIn("c_values = [0.10, 0.20]", runner_text)
        self.assertIn("random_count = 20", runner_text)
        self.assertIn('"PILOT_NON_CONFIRMATORY"', runner_text)

    def test_full_protocol_is_frozen_before_confirmation(self):
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        actual = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        self.assertEqual(actual, lock["protocol_sha256"])
        self.assertEqual(lock["pilot_seeds"], [100, 101, 102])
        self.assertEqual(lock["confirmation_seeds"], list(range(10)))
        self.assertTrue(set(lock["pilot_seeds"]).isdisjoint(lock["confirmation_seeds"]))
        self.assertEqual(lock["confirmation_c_values"], [0.02, 0.05, 0.10, 0.20])
        self.assertEqual(lock["random_candidates"], 97)
        self.assertEqual(lock["acceptance"]["completed_fits"], 40)

    def test_full_runner_uses_supplementary_status(self):
        runner = load_module(
            ROOT / "tools" / "run_asd_001r_full.py", "asd001r_full_tests"
        )
        lock, historical_hash = runner.verify_frozen_inputs()
        config = runner.configuration(lock, historical_hash)
        self.assertEqual(config["execution_mode"], "FULL_CONFIRMATORY_SUPPLEMENT")
        self.assertEqual(config["random_candidates"], 97)
        self.assertEqual(config["max_iter"], 5000)
        self.assertFalse(
            runner.compare_with_publication(
                {
                    key: {
                        "fits": 0,
                        "structural_passes": 0,
                        "top1_true": 0,
                        "both_true_top10": 0,
                        "both_true_top2": 0,
                        "mean_best_rank": 100.0,
                        "mean_worst_rank": 100.0,
                        "positive_true_importances": 0,
                        "positive_margin_over_random": 0,
                        "positive_combined_ablation_gain": 0,
                        "convergence_warnings": 0,
                        "accuracy": value,
                    }
                    for key, value in runner.EXPECTED_ACCURACY.items()
                },
                {},
                40,
            )["historical_exact_reproduction"]
        )

    def test_red_is_reserved_for_real_errors(self):
        for name in [
            "RUN_STAGE_06_ASD_001R_PILOT.ps1",
            "RUN_STAGE_06_ASD_001R_FULL.ps1",
            "APPLY_STAGE_06_ASD_001R_CLOSEOUT.ps1",
        ]:
            script = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", script)
            self.assertIn("ForegroundColor Green", script)


if __name__ == "__main__":
    unittest.main()
