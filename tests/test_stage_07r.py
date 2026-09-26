import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
BASE = ROOT / "experiments" / "05_permutation_and_representation_supplementary"
IDS = ["PL-002R", "PL-003R", "HD-003R", "CMP-001R", "CMP-002R"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage07RTests(unittest.TestCase):
    def test_original_chronology_remains_unchanged(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 115)
        self.assertFalse(set(IDS) & {row["id"] for row in rows})

    def test_supplementary_inventory_is_separate(self):
        with (ROOT / "inventory" / "supplementary_experiments.csv").open(encoding="utf-8", newline="") as stream:
            rows = {row["id"]: row for row in csv.DictReader(stream)}
        expected = {
            "PL-002R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
            "PL-003R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
            "HD-003R": "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED",
            "CMP-001R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
            "CMP-002R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        }
        for experiment_id in IDS:
            self.assertIn(experiment_id, rows)
            self.assertEqual(rows[experiment_id]["relationship_to_pdf"], "OUTSIDE_115_PDF_CHRONOLOGY")
            self.assertEqual(rows[experiment_id]["protocol_status"], "FROZEN_BEFORE_CONFIRMATION")
            self.assertEqual(rows[experiment_id]["reproduction_status"], expected[experiment_id])

    def test_every_unit_denies_historical_source_claim(self):
        for experiment_id in IDS:
            provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
            self.assertFalse(provenance["historical_source_claimed"])
            self.assertEqual(provenance["relationship_to_pdf"], "OUTSIDE_115_PDF_CHRONOLOGY")
            self.assertEqual(provenance["protocol_status"], "FROZEN_BEFORE_CONFIRMATION")

    def test_confirmation_seeds_are_separate_from_pilot(self):
        protocol = json.loads((BASE / "STAGE_07R_PROTOCOL.json").read_text(encoding="utf-8"))
        self.assertNotEqual(protocol["pilot"]["seed"], protocol["full"]["pl2_evolution_seed"])
        self.assertNotEqual(protocol["pilot"]["seed"], protocol["full"]["pl3_seed"])
        self.assertTrue(set(protocol["pilot"]["hd_seeds"]).isdisjoint(protocol["full"]["hd_seeds"]))
        self.assertTrue(set(protocol["pilot"]["cmp_seeds"]).isdisjoint(protocol["full"]["cmp2_seeds"]))

    def test_protocol_lock_matches_critical_files(self):
        runner = load_module(ROOT / "tools" / "run_stage_07r.py", "stage07r_runner")
        lock = runner.validate_lock()
        self.assertEqual(lock["protocol_id"], "STAGE_07R_V1")
        self.assertEqual(lock["pilot_status"], "5_OF_5_STRUCTURAL_PILOT_PASS")

    def test_core_contains_no_published_target_accuracy_constants(self):
        source = (ROOT / "src" / "bohn_original" / "stage07_supplementary.py").read_text(encoding="utf-8")
        for value in ("0.9259", "0.9167", "0.9426", "0.7759", "0.897"):
            self.assertNotIn(value, source)

    def test_reconstruction_primitives(self):
        from bohn_original.stage07_supplementary import TRUE_FLIP, TRUE_ROT180, compression_representation, make_labels, z3_permutation

        x = np.arange(6 * 64, dtype=float).reshape(6, 64)
        self.assertEqual(compression_representation(x).shape, (6, 128))
        self.assertEqual(len(np.unique(TRUE_FLIP)), 64)
        self.assertEqual(len(np.unique(TRUE_ROT180)), 64)
        random_x = np.random.default_rng(7).normal(size=(80, 64))
        labels = make_labels(random_x, seed=42)
        self.assertEqual(set(labels), {0, 1})
        permutation = z3_permutation(63)
        np.testing.assert_array_equal(permutation[permutation[permutation]], np.arange(63))

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_07R.ps1", "RUN_STAGE_07R_PILOT.ps1", "RUN_STAGE_07R_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
