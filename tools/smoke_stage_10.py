#!/usr/bin/env python3
"""Lekka sonda strukturalna Etapu 10; nie zastępuje pełnego protokołu."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "08_meta_sbohn"
IDS = [f"MS-{number:03d}" for number in range(1, 11)]


def load_source(path: Path):
    spec = importlib.util.spec_from_file_location("stage10_smoke_source", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=IDS, required=True)
    args = parser.parse_args()
    provenance = json.loads((BASE / args.only / "provenance.json").read_text(encoding="utf-8"))
    if not provenance["listing_target_code_present"]:
        print(json.dumps({"id": args.only, "probe": "AUDIT_BOUNDARY_PASS"}))
        return 0

    source = BASE / args.only / "historical" / "source_from_monograph.py"
    module = load_source(source)
    mode = "fixed_geometry" if args.only == "MS-009" else "annealed_geometry"
    train_x, test_x, train_y, test_y = module.make_task_data(0, "easy")
    best, history = module.evolve_geometry_generator(
        train_x, test_x, train_y, test_y, task="easy", mode=mode,
        population_size=4, generations=1, elite_size=2, mutation_sigma=0.25, seed=100,
    )
    result = {
        "id": args.only,
        "probe": "SMOKE_PROBE_PASS",
        "mode": mode,
        "accuracy": float(best["accuracy"]),
        "geometry_score": float(best["geometry_score"]),
        "history_rows": len(history),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
