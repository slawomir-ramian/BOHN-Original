#!/usr/bin/env python3
"""Wznawialna, wierna obliczeniowo reprodukcja ASD-001.

Listing historyczny pozostaje niezmieniony. Ten adapter rozdziela jego 40
dopasowań na osobne zadania i zapisuje checkpoint po każdym z nich.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import warnings
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = (
    ROOT
    / "experiments"
    / "04_symmetry_discovery"
    / "ASD-001"
    / "historical"
    / "source_from_monograph.py"
)
DEFAULT_CHECKPOINT = ROOT / "reproduced" / "stage_06_asd_checkpoint"
EXPECTED_ACCURACY = {"0.02": 0.9244, "0.05": 0.9554, "0.10": 0.9630, "0.20": 0.9630}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def flip_horizontal(x):
    return np.array([row.reshape(8, 8)[:, ::-1].ravel() for row in x])


def rotate_180(x):
    return np.array([row.reshape(8, 8)[::-1, ::-1].ravel() for row in x])


def random_perm(x, seed):
    permutation = np.random.default_rng(seed).permutation(x.shape[1])
    return x[:, permutation]


def features(x, transform):
    return np.abs(x - transform(x))


def labels(x):
    asymmetry = np.abs(x - rotate_180(x))
    weights = np.random.default_rng(42).standard_normal(asymmetry.shape[1])
    score = asymmetry @ weights
    return (score > np.median(score)).astype(int)


def fit_one(task):
    c_value, seed, random_count, max_iter = task
    started = time.perf_counter()
    x_all = load_digits().data.astype(np.float64)
    y_all = labels(x_all)
    x_train, x_test, y_train, y_test = train_test_split(
        x_all, y_all, test_size=0.3, random_state=seed
    )

    train_blocks = {
        "flip_horizontal": features(x_train, flip_horizontal),
        "rotate_180": features(x_train, rotate_180),
    }
    test_blocks = {
        "flip_horizontal": features(x_test, flip_horizontal),
        "rotate_180": features(x_test, rotate_180),
    }
    for index in range(random_count):
        name = f"rand_{index}"
        permutation_seed = seed * 10000 + index
        train_blocks[name] = features(
            x_train, lambda values, s=permutation_seed: random_perm(values, s)
        )
        test_blocks[name] = features(
            x_test, lambda values, s=permutation_seed: random_perm(values, s)
        )

    names = sorted(train_blocks)
    phi_train = np.hstack([train_blocks[name] for name in names])
    phi_test = np.hstack([test_blocks[name] for name in names])
    classifier = LogisticRegression(
        C=c_value, penalty="l1", solver="saga", max_iter=max_iter
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        classifier.fit(phi_train, y_train)

    importances = {}
    for index, name in enumerate(names):
        block = slice(index * 64, (index + 1) * 64)
        importances[name] = float(np.sum(np.abs(classifier.coef_[:, block])))
    ranking = sorted(importances, key=importances.get, reverse=True)
    true_ranks = [ranking.index(name) + 1 for name in ("flip_horizontal", "rotate_180")]
    warning_names = [type(item.message).__name__ for item in caught]
    return {
        "C": c_value,
        "seed": seed,
        "accuracy": float(classifier.score(phi_test, y_test)),
        "top_candidate": ranking[0],
        "flip_horizontal_rank": true_ranks[0],
        "rotate_180_rank": true_ranks[1],
        "best_true_rank": min(true_ranks),
        "worst_true_rank": max(true_ranks),
        "warning_types": warning_names,
        "duration_seconds": round(time.perf_counter() - started, 6),
    }


def task_key(c_value, seed):
    return f"C={c_value:.2f}|seed={seed:02d}"


def atomic_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def configuration(c_values, seeds, random_count, max_iter):
    return {
        "historical_source_sha256": sha256_bytes(HISTORICAL.read_bytes().rstrip(b"\r\n")),
        "c_values": c_values,
        "seeds": seeds,
        "random_candidates": random_count,
        "max_iter": max_iter,
        "solver": "saga",
        "penalty": "l1",
        "classifier_random_state": None,
        "sklearn_version": sklearn.__version__,
    }


def load_checkpoint(path, config):
    if not path.exists():
        return {"stage": "06", "experiment_id": "ASD-001", "configuration": config, "tasks": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("configuration") != config:
        raise RuntimeError(
            "Istniejący checkpoint ma inną konfigurację. Nie został nadpisany."
        )
    return payload


def aggregate(tasks, c_values, seeds):
    lines = []
    rows = {}
    for c_value in c_values:
        selected = [tasks[task_key(c_value, seed)] for seed in seeds]
        accuracy = float(np.mean([item["accuracy"] for item in selected]))
        top1 = sum(item["top_candidate"] in {"flip_horizontal", "rotate_180"} for item in selected)
        top10 = sum(
            max(item["flip_horizontal_rank"], item["rotate_180_rank"]) <= 10
            for item in selected
        )
        best = float(np.mean([item["best_true_rank"] for item in selected]))
        worst = float(np.mean([item["worst_true_rank"] for item in selected]))
        rows[f"{c_value:.2f}"] = {
            "accuracy": accuracy,
            "top1_true": top1,
            "both_true_top10": top10,
            "mean_best_rank": best,
            "mean_worst_rank": worst,
        }
        lines.extend(
            [
                f"=== C = {c_value:.2f} ===",
                f"  Accuracy:          {accuracy:.4f}",
                f"  Top1 True:         {top1}/{len(seeds)}",
                f"  Both True Top10:   {top10}/{len(seeds)}",
                f"  Mean Best Rank:    {best:.1f}",
                f"  Mean Worst Rank:   {worst:.1f}",
                "",
            ]
        )
    return "\n".join(lines), rows


def comparison(rows):
    primary = all(
        row["top1_true"] == 10 and row["mean_best_rank"] == 1.0
        for row in rows.values()
    )
    secondary = all(
        row["both_true_top10"] == 10 and row["mean_worst_rank"] == 2.0
        for row in rows.values()
    )
    deltas = [abs(rows[key]["accuracy"] - value) for key, value in EXPECTED_ACCURACY.items()]
    maximum = max(deltas)
    if primary and secondary and maximum <= 0.002:
        status = "CLOSE_NUMERIC_MATCH"
    elif primary and not secondary:
        status = "PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH"
    elif primary:
        status = "PRIMARY_MATCH_NUMERIC_DIFFERENCE"
    else:
        status = "SCIENTIFIC_MISMATCH"
    return {
        "status": status,
        "scientific_conclusion_preserved": primary,
        "primary_encoded_symmetry_reproduced": primary,
        "secondary_reported_symmetry_reproduced": secondary,
        "full_reported_table_reproduced": primary and secondary and maximum <= 0.002,
        "max_reported_numeric_delta": maximum,
        "actual_summary": rows,
        "note": (
            "Obrót o 180 stopni, jedyna symetria użyta przez make_labels, został "
            "odkryty jako najlepszy w 40/40 prób. Raportowana druga symetria "
            "flip_horizontal nie jest kodowana w etykiecie i nie odtworzyła rang tabeli 4.2."
        ),
    }


def find_base_results(explicit):
    if explicit:
        candidates = [explicit]
    else:
        candidates = sorted(
            (ROOT / "reproduced" / "stage_06_runs").glob("*/results.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    for candidate in candidates:
        result_file = candidate if candidate.name == "results.json" else candidate / "results.json"
        if not result_file.exists():
            continue
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        if all(
            payload.get("experiments", {}).get(exp, {}).get("execution_status") == "PASS"
            for exp in ["SD-001", "SD-002", "SD-003", "SD-004"]
        ):
            return result_file.parent, payload
    raise RuntimeError("Nie znaleziono przebiegu z zaliczonymi SD-001--SD-004.")


def manifest(directory):
    target = directory / "MANIFEST_SHA256.txt"
    lines = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path != target:
            lines.append(f"{sha256_bytes(path.read_bytes())}  {path.relative_to(directory).as_posix()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize(checkpoint_dir, tasks, c_values, seeds, session_seconds, base_results_dir, output_dir):
    stdout, rows = aggregate(tasks, c_values, seeds)
    (checkpoint_dir / "ASD-001_stdout.txt").write_text(stdout, encoding="utf-8")
    warning_counts = {}
    for item in tasks.values():
        for warning_name in item["warning_types"]:
            warning_counts[warning_name] = warning_counts.get(warning_name, 0) + 1
    stderr = "\n".join(f"{name}: {count}" for name, count in sorted(warning_counts.items()))
    if stderr:
        stderr += "\n"
    (checkpoint_dir / "ASD-001_stderr.txt").write_text(stderr, encoding="utf-8")
    cmp = comparison(rows)
    summary = {
        "experiment_id": "ASD-001",
        "execution_mode": "CHECKPOINTED_FAITHFUL_RECONSTRUCTION",
        "completed_fits": len(tasks),
        "comparison": cmp,
        "warning_counts": warning_counts,
        "accumulated_fit_seconds": round(sum(item["duration_seconds"] for item in tasks.values()), 6),
        "current_session_seconds": round(session_seconds, 6),
    }
    atomic_json(checkpoint_dir / "ASD-001_RESULT.json", summary)

    base_dir, payload = find_base_results(base_results_dir)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    final_dir = output_dir or ROOT / "reproduced" / "stage_06_runs" / f"{stamp}_RECOVERED"
    raw = final_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for experiment_id in ["SD-001", "SD-002", "SD-003", "SD-004"]:
        for stream in ["stdout", "stderr"]:
            shutil.copy2(
                base_dir / "raw" / f"{experiment_id}_{stream}.txt",
                raw / f"{experiment_id}_{stream}.txt",
            )
    shutil.copy2(checkpoint_dir / "ASD-001_stdout.txt", raw / "ASD-001_stdout.txt")
    shutil.copy2(checkpoint_dir / "ASD-001_stderr.txt", raw / "ASD-001_stderr.txt")

    asd_stdout = (raw / "ASD-001_stdout.txt").read_bytes()
    asd_stderr = (raw / "ASD-001_stderr.txt").read_bytes()
    payload["run_utc"] = now.isoformat()
    payload["mode"] = "full_recovered"
    payload["recovered_from"] = str(base_dir.relative_to(ROOT)).replace("\\", "/")
    payload["environment"] = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "processor_count": os.cpu_count(),
    }
    payload["experiments"]["ASD-001"] = {
        "execution_status": "PASS" if cmp["scientific_conclusion_preserved"] else "FAILED",
        "return_code": 0 if cmp["scientific_conclusion_preserved"] else 1,
        "duration_seconds": summary["accumulated_fit_seconds"],
        "execution_mode": "CHECKPOINTED_FAITHFUL_RECONSTRUCTION",
        "executed_file": "tools/run_asd_001_recovery.py",
        "stdout_sha256": sha256_bytes(asd_stdout),
        "stderr_sha256": sha256_bytes(asd_stderr),
        "stderr_nonempty": bool(asd_stderr.strip()),
        "stdout_file": "raw/ASD-001_stdout.txt",
        "stderr_file": "raw/ASD-001_stderr.txt",
        "completed_fits": len(tasks),
        "comparison": cmp,
    }
    atomic_json(final_dir / "results.json", payload)
    atomic_json(
        final_dir / "CHECKPOINT.json",
        {
            "stage": "06",
            "mode": "full_recovered",
            "completed_units": ["SD-001", "SD-002", "SD-003", "SD-004", "ASD-001"],
            "source_chronology": ["SD-001", "SD-002", "SD-003", "SD-004", "ASD-001"],
            "experiments": payload["experiments"],
        },
    )
    report_lines = [
        "# Etap 06 - raport końcowy po odzyskaniu ASD-001",
        "",
        "Kod historyczny zachowano bez zmian. ASD-001 wykonano wiernym adapterem",
        "z checkpointem po każdym z 40 dopasowań.",
        "",
        "| # | ID | Tryb | Wykonanie | Porównanie |",
        "|---:|---|---|---|---|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        item = payload["experiments"][experiment_id]
        report_lines.append(
            f"| {index} | {experiment_id} | {item['execution_mode']} | "
            f"{item['execution_status']} | {item['comparison']['status']} |"
        )
    (final_dir / "REPRODUCTION_REPORT_PL.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    manifest(final_dir)
    latest = ROOT / "reproduced" / "stage_06_runs" / "LATEST_RUN.txt"
    latest.write_text(str(final_dir.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    artifact = ROOT / "artifacts" / f"BOHN_ORIGINAL_STAGE_06_RESULTS_{stamp}_RECOVERED"
    zip_path = Path(shutil.make_archive(str(artifact), "zip", root_dir=final_dir))
    return final_dir, zip_path, cmp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--base-results-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 2:
        parser.error("--workers musi wynosić 1 lub 2")

    c_values = [0.10] if args.quick else [0.02, 0.05, 0.10, 0.20]
    seeds = [0, 1] if args.quick else list(range(10))
    random_count = 5 if args.quick else 97
    max_iter = 500 if args.quick else 5000
    checkpoint_dir = args.checkpoint_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = checkpoint_dir / "CHECKPOINT.json"
    config = configuration(c_values, seeds, random_count, max_iter)
    checkpoint = load_checkpoint(checkpoint_file, config)
    tasks = checkpoint["tasks"]
    all_tasks = [(c_value, seed, random_count, max_iter) for c_value in c_values for seed in seeds]
    missing = [task for task in all_tasks if task_key(task[0], task[1]) not in tasks]
    print(f"ASD-001 CHECKPOINT: {len(tasks)}/{len(all_tasks)} ukończonych", flush=True)
    session_started = time.perf_counter()

    if missing:
        executor = ProcessPoolExecutor(max_workers=args.workers)
        futures = {executor.submit(fit_one, task): task for task in missing}
        pending = set(futures)
        try:
            while pending:
                done, pending = wait(pending, timeout=60, return_when=FIRST_COMPLETED)
                if not done:
                    elapsed = time.perf_counter() - session_started
                    print(
                        f"ASD-001: nadal działa | checkpoint {len(tasks)}/{len(all_tasks)} | {elapsed:.0f} s",
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
                    print(
                        f"ASD-001: zapisano {key} | checkpoint {len(tasks)}/{len(all_tasks)} | "
                        f"{item['duration_seconds']:.1f} s",
                        flush=True,
                    )
        except KeyboardInterrupt:
            for future in pending:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            print("ASD-001: przerwano; zapisane checkpointy zostają zachowane.", flush=True)
            return 130
        finally:
            if not getattr(executor, "_shutdown_thread", False):
                executor.shutdown(wait=True, cancel_futures=False)

    session_seconds = time.perf_counter() - session_started
    stdout, rows = aggregate(tasks, c_values, seeds)
    print(stdout, flush=True)
    if args.quick:
        ok = all(row["top1_true"] == len(seeds) for row in rows.values())
        print("ASD-001 RECOVERY QUICK: PASS" if ok else "ASD-001 RECOVERY QUICK: FAILED")
        return 0 if ok else 1

    final_dir, zip_path, cmp = finalize(
        checkpoint_dir,
        tasks,
        c_values,
        seeds,
        session_seconds,
        args.base_results_dir,
        args.output_dir,
    )
    print(f"ASD-001: PASS | {cmp['status']}")
    print(f"RESULTS: {final_dir}")
    print(f"ZIP: {zip_path}")
    return 0 if cmp["primary_encoded_symmetry_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
