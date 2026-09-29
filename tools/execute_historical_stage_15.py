#!/usr/bin/env python3
"""Wykonaj pełny listing 71 przez jawny wrapper checkpointów komórek."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ["RF-001", "RF-002", "MF-001", "MF-002", "MF-003", "MF-004", "MF-005"]
PROGRAMS = ["v1", "testA", "v2", "v3", "v4", "v5"]
NOISES = [0.0, 0.1, 0.3, 0.5]
N_SAMPLES = 6000
N_SEEDS = 10


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_suite(source: Path):
    spec = importlib.util.spec_from_file_location("bohn_stage15_historical_suite", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def standard_rows(suite, X, y, seed: int, noise: float) -> list[dict]:
    return [dict(seed=seed, noise=noise, **row, extra="") for row in suite.evaluate_standard_reps(X, y, seed)]


def execute_cell(suite, program: str, seed: int, noise: float | None) -> dict:
    if program == "v1":
        return {"rows": suite.run_v1(seed, N_SAMPLES, 0.10), "library": []}

    X = suite.generate_signals(N_SAMPLES, seed)
    y = suite.make_out_of_representation_labels(X, seed + 123, noise=float(noise))
    rows = standard_rows(suite, X, y, seed, float(noise))
    library_rows = []
    offset = int(float(noise) * 1000)

    if program == "v2":
        for mode, label, extra_seed in [
                ("global", "Meta-FBOHN-v1-global", 111),
                ("orbitwise", "Meta-FBOHN-v2-orbitwise", 222)]:
            best, _ = suite.evolve_weighted_meta(
                X, y, seed + offset + extra_seed, mode, pop=80, generations=30, elite=8)
            features = (suite.weighted_fbohn_global(X, best["theta"])
                        if mode == "global" else suite.weighted_fbohn_orbitwise(X, best["theta"]))
            rows.append(dict(seed=seed, noise=noise, representation=label,
                             feature_dim=features.shape[1],
                             accuracy=suite.evaluate_features_split(features, y, seed),
                             extra=str(suite.np.round(suite.softplus(best["theta"]), 4).tolist())))
    elif program == "v3":
        best, _ = suite.evolve_mixing_v3(
            X, y, seed + offset + 333, mix_features=12, pop=80, generations=30, elite=8)
        features = suite.meta_fbohn_v3_features(X, best["theta"], 12, True)
        rows.append(dict(seed=seed, noise=noise, representation="Meta-FBOHN-v3-mixing",
                         feature_dim=features.shape[1],
                         accuracy=suite.evaluate_features_split(features, y, seed), extra="theta omitted"))
    elif program in {"v4", "v5"}:
        best, _ = suite.evolve_symbolic_composer(
            X, y, seed + offset + 444, pop=80, generations=30, elite=8, n_symbolic_features=16)
        features = suite.symbolic_fbohn_features(X, best["genome"], True)
        rows.append(dict(seed=seed, noise=noise, representation="Meta-FBOHN-v4-single",
                         feature_dim=features.shape[1],
                         accuracy=suite.evaluate_features_split(features, y, seed),
                         extra=str(suite.genome_to_strings(best["genome"]))))
        if program == "v5":
            library, library_df, _ = suite.discover_library_for_dataset(
                X, y, seed + offset + 555, runs=12, library_size=32,
                pop=80, generations=30, elite=8, n_symbolic_features=16)
            features = suite.symbolic_fbohn_features(X, [suite.key_to_gene(key) for key in library], True)
            rows.append(dict(seed=seed, noise=noise, representation="Meta-FBOHN-v5-library",
                             feature_dim=features.shape[1],
                             accuracy=suite.evaluate_features_split(features, y, seed),
                             extra=str([suite.gene_to_string(suite.key_to_gene(key)) for key in library])))
            library_rows = library_df.to_dict(orient="records")
    return {"rows": rows, "library": library_rows}


def cell_name(program: str, seed: int, noise: float | None) -> str:
    return f"seed_{seed:02d}.json" if program == "v1" else f"noise_{float(noise):.1f}_seed_{seed:02d}.json"


def aggregate(suite, program: str, cells: list[dict]) -> dict:
    rows = [row for cell in cells for row in cell["rows"]]
    frame = suite.pd.DataFrame(rows)
    group = ["representation"] if program == "v1" else ["noise", "representation"]
    summary = (frame.groupby(group)
               .agg(acc_mean=("accuracy", "mean"), acc_std=("accuracy", "std"),
                    feature_dim=("feature_dim", "mean"))
               .reset_index().to_dict(orient="records"))
    payload = {"program": program, "protocol": {"samples": N_SAMPLES, "seeds": N_SEEDS,
               "noises": [] if program == "v1" else NOISES,
               "population": 80, "generations": 30, "elite": 8,
               "mix_features": 12, "n_symbolic": 16,
               "discovery_runs": 12 if program == "v5" else 0,
               "library_size": 32 if program == "v5" else 0},
               "rows": rows, "summary": summary}
    if program == "v5":
        libraries = [row for cell in cells for row in cell.get("library", [])]
        counts = {}
        symbols = {}
        for row in libraries:
            counts[row["operator"]] = counts.get(row["operator"], 0) + int(row["count"])
            symbol = row["symbol"]
            symbols[symbol] = symbols.get(symbol, 0) + int(row["count"])
        payload["operator_counts"] = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
        payload["symbol_counts"] = dict(sorted(symbols.items(), key=lambda item: item[1], reverse=True)[:80])
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", choices=PROGRAMS, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()

    canonical = ROOT / "experiments" / "13_rmig_meta_fbohn" / "RF-001"
    source = canonical / "historical" / "source_from_monograph.py"
    provenance = json.loads((canonical / "provenance.json").read_text(encoding="utf-8"))
    expected = provenance["historical_source_sha256"][0]
    original = source.read_text(encoding="utf-8")
    if hashlib.sha256(original.encode()).hexdigest() != expected:
        raise SystemExit("Historical source hash mismatch")
    suite = load_suite(source)

    cells_dir = args.checkpoint / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    cell_specs = ([(seed, None) for seed in range(N_SEEDS)] if args.program == "v1"
                  else [(seed, noise) for noise in NOISES for seed in range(N_SEEDS)])
    completed = 0
    cells = []
    for seed, noise in cell_specs:
        path = cells_dir / cell_name(args.program, seed, noise)
        if path.is_file():
            try:
                cell = json.loads(path.read_text(encoding="utf-8"))
                cells.append(cell)
                completed += 1
                continue
            except (json.JSONDecodeError, KeyError):
                path.unlink()
        cell = execute_cell(suite, args.program, seed, noise)
        write_json(path, cell)
        cells.append(json_safe(cell))
        completed += 1
        write_json(args.checkpoint / "progress.json", {
            "program": args.program, "completed": completed, "total": len(cell_specs),
            "last_seed": seed, "last_noise": noise})
        print(f"CELL {args.program}: {completed}/{len(cell_specs)} | seed={seed} | noise={noise}", flush=True)

    payload = aggregate(suite, args.program, cells)
    write_json(args.checkpoint / "summary.json", payload)
    write_json(args.checkpoint / "complete.json", {"program": args.program, "cells": len(cells), "status": "PASS"})
    if hashlib.sha256(source.read_text(encoding="utf-8").encode()).hexdigest() != expected:
        raise SystemExit("Historical source changed")
    print(f"PROGRAM {args.program}: PASS | cells={len(cells)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
