#!/usr/bin/env python3
"""Wznawialny pilot jawnej rekonstrukcji ASD-001R."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_FILE = (
    ROOT
    / "experiments"
    / "04_symmetry_discovery"
    / "ASD-001"
    / "reconstruction"
    / "two_symmetry_protocol.py"
)
HISTORICAL_FILE = (
    ROOT
    / "experiments"
    / "04_symmetry_discovery"
    / "ASD-001"
    / "historical"
    / "source_from_monograph.py"
)
DEFAULT_CHECKPOINT = ROOT / "reproduced" / "stage_06_asd_001r_pilot_checkpoint"


def load_protocol():
    spec = importlib.util.spec_from_file_location("asd_001r_protocol", PROTOCOL_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_task(task):
    """Top-level worker bezpieczny dla mechanizmu spawn w Windows."""
    return load_protocol().fit_pilot_task(task)


def sha256(path):
    return hashlib.sha256(path.read_bytes().rstrip(b"\r\n")).hexdigest()


def atomic_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def task_key(c_value, seed):
    return f"C={c_value:.2f}|seed={seed}"


def configuration(c_values, seeds, random_count, max_iter):
    return {
        "experiment_id": "ASD-001R",
        "status": "PILOT_NON_CONFIRMATORY",
        "protocol_sha256": sha256(PROTOCOL_FILE),
        "historical_source_sha256": sha256(HISTORICAL_FILE),
        "c_values": c_values,
        "seeds": seeds,
        "random_candidates": random_count,
        "max_iter": max_iter,
        "solver": "saga",
        "l1_ratio": 1.0,
        "classifier_random_state": "split_seed",
        "sklearn_version": sklearn.__version__,
    }


def load_checkpoint(path, config):
    if not path.exists():
        return {"configuration": config, "tasks": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("configuration") != config:
        raise RuntimeError(
            "Istniejący checkpoint pilota ma inną konfigurację i nie został nadpisany."
        )
    return payload


def task_pass(item):
    raw_ranks = list(item["true_ranks"].values())
    ranks = sorted(raw_ranks) if all(rank is not None for rank in raw_ranks) else []
    ablation = item["oracle_ablation"]["accuracy"]
    convergence_warning = "ConvergenceWarning" in item["warning_types"]
    return (
        ranks == [1, 2]
        and min(item["true_importances"].values()) > 1e-10
        and item["min_true_margin_over_best_random"] > 0.0
        and not convergence_warning
        and ablation["combined_gain"] > 0.0
    )


def aggregate(tasks, c_values, seeds):
    rows = {}
    for c_value in c_values:
        selected = [tasks[task_key(c_value, seed)] for seed in seeds]
        rows[f"{c_value:.2f}"] = {
            "fits": len(selected),
            "structural_passes": sum(task_pass(item) for item in selected),
            "mean_accuracy": float(np.mean([item["accuracy"] for item in selected])),
            "both_true_top2": sum(
                all(rank is not None for rank in item["true_ranks"].values())
                and sorted(item["true_ranks"].values()) == [1, 2]
                for item in selected
            ),
            "positive_true_importances": sum(
                min(item["true_importances"].values()) > 1e-10 for item in selected
            ),
            "positive_margin_over_random": sum(
                item["min_true_margin_over_best_random"] > 0.0 for item in selected
            ),
            "mean_combined_ablation_gain": float(
                np.mean(
                    [
                        item["oracle_ablation"]["accuracy"]["combined_gain"]
                        for item in selected
                    ]
                )
            ),
        }
    total = len(c_values) * len(seeds)
    passed = sum(task_pass(item) for item in tasks.values())
    grade = "STRUCTURAL_PILOT_PASS" if passed == total else "PILOT_NEEDS_REVISION"
    return rows, passed, total, grade


def manifest(directory):
    target = directory / "MANIFEST_SHA256.txt"
    lines = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path != target:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(directory).as_posix()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output, payload):
    lines = [
        "# ASD-001R — raport pilota rekonstrukcyjnego",
        "",
        "**Status: PILOT_NON_CONFIRMATORY.** Ten wynik nie potwierdza historycznej",
        "tabeli 4.2 i nie dowodzi istnienia nieopublikowanej wersji kodu.",
        "",
        f"Ocena strukturalna: **{payload['pilot_grade']}** ",
        f"({payload['structural_passes']}/{payload['total_fits']} dopasowań).",
        "",
        "| C | Dopasowania | Sukces strukturalny | Obie prawdziwe Top2 | Dodatnie ważności | Dodatni margines | Accuracy | Gain ablacj. |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c_value, row in payload["summary_by_c"].items():
        lines.append(
            f"| {c_value} | {row['fits']} | {row['structural_passes']} | "
            f"{row['both_true_top2']} | {row['positive_true_importances']} | "
            f"{row['positive_margin_over_random']} | {row['mean_accuracy']:.4f} | "
            f"{row['mean_combined_ablation_gain']:.4f} |"
        )
    lines += [
        "",
        "Pełne rangi, ważności, kolejności kandydatów, ostrzeżenia i wyniki ablacji",
        "znajdują się w `results.json`.",
        "",
        "Następny krok wymaga zamrożenia protokołu przed uruchomieniem seedów",
        "historycznych i pełnych 97 kandydatów.",
    ]
    (output / "REPORT_PL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize(checkpoint, config, session_seconds):
    tasks = checkpoint["tasks"]
    c_values = config["c_values"]
    seeds = config["seeds"]
    rows, passed, total, grade = aggregate(tasks, c_values, seeds)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "reproduced" / "stage_06_asd_001r_pilot" / stamp
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment_id": "ASD-001R",
        "relationship_to_original": "SEPARATE_EXPLICIT_RECONSTRUCTION",
        "epistemic_status": "PILOT_NON_CONFIRMATORY",
        "run_utc": now.isoformat(),
        "configuration": config,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "processor_count": os.cpu_count(),
        },
        "pilot_grade": grade,
        "structural_passes": passed,
        "total_fits": total,
        "summary_by_c": rows,
        "tasks": tasks,
        "current_session_seconds": round(session_seconds, 6),
        "interpretation_limit": (
            "Pilot tests a declared corrected mechanism; it does not establish "
            "which unpublished code version generated table 4.2."
        ),
    }
    atomic_json(output / "results.json", payload)
    write_report(output, payload)
    manifest(output)
    latest = ROOT / "reproduced" / "stage_06_asd_001r_pilot" / "LATEST_RUN.txt"
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    artifact = ROOT / "artifacts" / f"BOHN_ORIGINAL_STAGE_06_ASD_001R_PILOT_{stamp}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    zip_path = Path(shutil.make_archive(str(artifact), "zip", root_dir=output))
    return output, zip_path, payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()
    if not 1 <= args.workers <= 2:
        parser.error("--workers musi wynosić 1 lub 2")

    c_values = [0.10, 0.20]
    seeds = [100, 101, 102]
    random_count = 20
    max_iter = 2500
    config = configuration(c_values, seeds, random_count, max_iter)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = args.checkpoint_dir / "CHECKPOINT.json"
    checkpoint = load_checkpoint(checkpoint_file, config)
    tasks = checkpoint["tasks"]
    all_tasks = [
        (c_value, seed, random_count, max_iter)
        for c_value in c_values
        for seed in seeds
    ]
    missing = [task for task in all_tasks if task_key(task[0], task[1]) not in tasks]
    print(f"ASD-001R PILOT: checkpoint {len(tasks)}/{len(all_tasks)}", flush=True)
    started = time.perf_counter()
    if missing:
        executor = ProcessPoolExecutor(max_workers=args.workers)
        futures = {executor.submit(run_task, task): task for task in missing}
        pending = set(futures)
        try:
            while pending:
                done, pending = wait(pending, timeout=60, return_when=FIRST_COMPLETED)
                if not done:
                    elapsed = time.perf_counter() - started
                    print(
                        f"ASD-001R: nadal działa | checkpoint {len(tasks)}/{len(all_tasks)} | {elapsed:.0f} s",
                        flush=True,
                    )
                    continue
                for future in done:
                    task = futures[future]
                    item = future.result()
                    key = task_key(task[0], task[1])
                    tasks[key] = item
                    checkpoint["tasks"] = tasks
                    checkpoint["updated_utc"] = datetime.now(timezone.utc).isoformat()
                    atomic_json(checkpoint_file, checkpoint)
                    label = "PASS" if task_pass(item) else "REVIEW"
                    print(
                        f"ASD-001R: {key} | {label} | checkpoint "
                        f"{len(tasks)}/{len(all_tasks)} | {item['duration_seconds']:.1f} s",
                        flush=True,
                    )
        except KeyboardInterrupt:
            for future in pending:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            print("ASD-001R: przerwano; checkpointy pozostają zachowane.", flush=True)
            return 130
        finally:
            if not getattr(executor, "_shutdown_thread", False):
                executor.shutdown(wait=True, cancel_futures=False)

    output, zip_path, payload = finalize(
        checkpoint, config, time.perf_counter() - started
    )
    print(f"ASD-001R: PILOT_NON_CONFIRMATORY | {payload['pilot_grade']}")
    print(f"STRUCTURAL: {payload['structural_passes']}/{payload['total_fits']}")
    print(f"RESULTS: {output}")
    print(f"ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
