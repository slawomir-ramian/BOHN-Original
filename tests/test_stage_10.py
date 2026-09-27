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
BASE = ROOT / "experiments" / "08_meta_sbohn"
IDS = [f"MS-{number:03d}" for number in range(1, 11)]
EXECUTABLE = {"MS-009", "MS-010"}
FRAGMENTS = {"MS-005", "MS-006", "MS-007", "MS-008"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage10Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        with (ROOT / "inventory" / "source_chronology.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows[72:82]], IDS)
        self.assertEqual([int(row["source_order"]) for row in rows[72:82]], list(range(73, 83)))

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
                self.assertEqual(provenance["source_code_level"], "FULL_SHARED_LISTING")
                self.assertEqual(provenance["execution_mode"], "HISTORICAL_SOURCE")
            elif experiment_id in FRAGMENTS:
                self.assertFalse(provenance["listing_target_code_present"])
                self.assertEqual(provenance["source_code_level"], "SOURCE_FRAGMENT_ONLY")
                self.assertEqual(provenance["historical_source_files"], ["source_fragment_from_monograph.py"])
            else:
                self.assertFalse(provenance["listing_target_code_present"])
                self.assertEqual(provenance["source_code_level"], "NARRATIVE_ONLY")
                self.assertEqual(provenance["historical_source_files"], [])

    def test_shared_listing_hashes(self):
        full = {
            json.loads((BASE / item / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for item in EXECUTABLE
        }
        fragments = {
            json.loads((BASE / item / "provenance.json").read_text(encoding="utf-8"))["historical_source_sha256"][0]
            for item in FRAGMENTS
        }
        self.assertEqual(len(full), 1)
        self.assertEqual(len(fragments), 1)
        self.assertNotEqual(full, fragments)

    def test_historical_protocol_is_exact(self):
        source = load_module(BASE / "MS-009" / "historical" / "source_from_monograph.py", "stage10_historical_contract")
        self.assertEqual(source.SEEDS, list(range(20)))
        self.assertEqual(source.TASKS, ["easy", "medium", "hard"])
        self.assertEqual(source.POPULATION_SIZE, 60)
        self.assertEqual(source.GENERATIONS, 25)
        self.assertEqual(source.ELITE_SIZE, 6)

    def test_meta_sbohn_primitives(self):
        from bohn_original.meta_sbohn import geometry_features, initialize_population, lambda_schedule, theta_to_perm

        features = geometry_features()
        self.assertEqual(features.shape, (64, 14))
        permutation = theta_to_perm(np.arange(14, dtype=float), features)
        self.assertEqual(sorted(permutation.tolist()), list(range(64)))
        self.assertEqual(lambda_schedule("annealed_geometry", 0, 25), 0.12)
        self.assertEqual(lambda_schedule("annealed_geometry", 24, 25), 0.0)
        rng = np.random.default_rng(10)
        population = initialize_population(rng, 10, init_theta=np.zeros(14), mode="mixed")
        self.assertEqual(len(population), 10)
        self.assertTrue(all(value.shape == (14,) for value in population))

    def test_checkpoint_protocol_contract(self):
        executor = load_module(ROOT / "tools" / "execute_historical_stage_10.py", "stage10_executor")
        source = BASE / "MS-009" / "historical" / "source_from_monograph.py"
        contract = executor.protocol(source)
        self.assertEqual(contract["expected_cells"], 180)
        self.assertEqual(contract["population_size"], 60)
        self.assertEqual(contract["generations"], 25)
        self.assertEqual(len({executor.cell_name(seed, task, mode) for seed in range(20) for task in executor.TASKS for mode in executor.MODES}), 180)

    def test_runner_classifies_reference_shape(self):
        runner = load_module(ROOT / "tools" / "run_stage_10.py", "stage10_runner")
        summary = {
            mode: {task: {"final_acc": 0.0, "best_task_sim": 0.0, "acc092_and_sim025": 0.0} for task in ("easy", "medium", "hard")}
            for mode in ("accuracy_only", "fixed_geometry", "annealed_geometry")
        }
        for (mode, task, metric), value in runner.PUBLISHED["MS-010"].items():
            summary[mode][task][metric] = value
        summary["annealed_geometry"]["medium"]["acc092_and_sim025"] = 0.15
        summary["annealed_geometry"]["hard"]["acc092_and_sim025"] = 0.05
        self.assertEqual(runner.comparison("MS-010", {"summary": summary})["status"], "CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for name in ("SETUP_STAGE_10.ps1", "RUN_STAGE_10_SMOKE.ps1", "RUN_STAGE_10_FULL.ps1"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("ForegroundColor Red", text)
            self.assertIn("ForegroundColor Green", text)


if __name__ == "__main__":
    unittest.main()
