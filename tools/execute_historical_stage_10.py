#!/usr/bin/env python3
"""Checkpointowany wykonawca niezmienionego programu Meta-SBOHN v5/v6."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SEEDS = list(range(20))
TASKS = ["easy", "medium", "hard"]
MODES = ["accuracy_only", "fixed_geometry", "annealed_geometry"]
METRICS = [
    "baseline_acc", "true_acc", "final_acc", "gain_over_baseline", "gap_to_true",
    "best_task_sim", "geometry_score", "auc", "acc_ge_092", "sim_ge_025",
    "acc092_and_sim025",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source(path: Path):
    spec = importlib.util.spec_from_file_location("stage10_historical_source", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_value(value):
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def cell_name(seed: int, task: str, mode: str) -> str:
    return f"seed_{seed:02d}__{task}__{mode}.json"


def write_json_atomic(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def execute_cell(source: Path, cells: Path, seed: int, task: str, mode: str) -> int:
    module = load_source(source)
    row = json_value(module.run_one(seed, task, mode))
    if int(row["seed"]) != seed or row["task"] != task or row["mode"] != mode:
        raise RuntimeError("Historyczny runner zwrócił niezgodną komórkę")
    write_json_atomic(cells / cell_name(seed, task, mode), row)
    return 0


def protocol(source: Path) -> dict:
    return {
        "protocol_id": "STAGE_10_HISTORICAL_V1",
        "source_sha256": digest(source),
        "seeds": SEEDS,
        "tasks": TASKS,
        "modes": MODES,
        "population_size": 60,
        "generations": 25,
        "elite_size": 6,
        "expected_cells": 180,
    }


def valid_cell(path: Path, seed: int, task: str, mode: str) -> bool:
    if not path.is_file():
        return False
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
        return int(row["seed"]) == seed and row["task"] == task and row["mode"] == mode
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


def worker_process(source: Path, run_dir: Path, seed: int, task: str, mode: str) -> tuple[int, str, str, int]:
    args = [
        sys.executable, "-u", str(Path(__file__).resolve()), str(source),
        "--run-dir", str(run_dir), "--cell", str(seed), task, mode,
    ]
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    key = cell_name(seed, task, mode).removesuffix(".json")
    logs = run_dir / "cell_logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{key}_stdout.txt").write_text(completed.stdout, encoding="utf-8", newline="\n")
    (logs / f"{key}_stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
    return seed, task, mode, completed.returncode


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for mode in MODES:
        summary[mode] = {}
        for task in TASKS:
            selected = [row for row in rows if row["mode"] == mode and row["task"] == task]
            summary[mode][task] = {
                metric: sum(float(row[metric]) for row in selected) / len(selected)
                for metric in METRICS
            }
    return summary


def execute_all(source: Path, run_dir: Path, workers: int) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    cells = run_dir / "cells"
    cells.mkdir(exist_ok=True)
    expected_protocol = protocol(source)
    protocol_path = run_dir / "PROTOCOL.json"
    if protocol_path.exists():
        existing = json.loads(protocol_path.read_text(encoding="utf-8"))
        if existing != expected_protocol:
            raise RuntimeError("Checkpoint pochodzi z innego kodu lub protokołu. Przenieś katalog stage_10_checkpoint i uruchom ponownie.")
    else:
        write_json_atomic(protocol_path, expected_protocol)

    jobs = [(seed, task, mode) for seed in SEEDS for task in TASKS for mode in MODES]
    completed_jobs = [job for job in jobs if valid_cell(cells / cell_name(*job), *job)]
    pending = [job for job in jobs if job not in completed_jobs]
    total = len(jobs)
    print(f"META-SBOHN: checkpoint {len(completed_jobs)}/{total} | workers={workers}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(worker_process, source, run_dir, *job): job for job in pending}
        while futures:
            done, _ = concurrent.futures.wait(
                futures, timeout=60, return_when=concurrent.futures.FIRST_COMPLETED
            )
            if not done:
                current = sum(valid_cell(cells / cell_name(*job), *job) for job in jobs)
                print(f"META-SBOHN: nadal działa | checkpoint {current}/{total}", flush=True)
                continue
            for future in done:
                job = futures.pop(future)
                seed, task, mode, return_code = future.result()
                if return_code != 0:
                    raise RuntimeError(f"Błąd komórki seed={seed}, task={task}, mode={mode}; sprawdź cell_logs.")
                completed_jobs.append(job)
                write_json_atomic(
                    run_dir / "CHECKPOINT.json",
                    {"completed": len(completed_jobs), "expected": total, "last_cell": {"seed": seed, "task": task, "mode": mode}},
                )
                print(f"META-SBOHN: {task}|{mode}|seed={seed} | PASS | checkpoint {len(completed_jobs)}/{total}", flush=True)

    rows = [json.loads((cells / cell_name(*job)).read_text(encoding="utf-8")) for job in jobs]
    payload = {"protocol": expected_protocol, "rows": rows, "summary": summarize(rows)}
    write_json_atomic(run_dir / "meta_sbohn_results.json", payload)
    print("META-SBOHN HISTORICAL EXECUTION: PASS", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--cell", nargs=3, metavar=("SEED", "TASK", "MODE"))
    args = parser.parse_args()
    source = args.source.resolve()
    run_dir = args.run_dir.resolve()
    if args.cell:
        seed_text, task, mode = args.cell
        return execute_cell(source, run_dir / "cells", int(seed_text), task, mode)
    if not 1 <= args.workers <= 8:
        raise SystemExit("workers musi należeć do 1..8")
    return execute_all(source, run_dir, args.workers)


if __name__ == "__main__":
    raise SystemExit(main())
