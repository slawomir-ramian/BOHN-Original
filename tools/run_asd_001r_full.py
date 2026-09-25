#!/usr/bin/env python3
"""Pełny, wznawialny bieg potwierdzający ASD-001R."""
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
RECONSTRUCTION = (
    ROOT / "experiments" / "04_symmetry_discovery" / "ASD-001" / "reconstruction"
)
PROTOCOL_FILE = RECONSTRUCTION / "two_symmetry_protocol.py"
LOCK_FILE = RECONSTRUCTION / "ASD-001R_PROTOCOL_LOCK.json"
HISTORICAL_FILE = RECONSTRUCTION.parent / "historical" / "source_from_monograph.py"
PROVENANCE_FILE = RECONSTRUCTION.parent / "provenance.json"
DEFAULT_CHECKPOINT = ROOT / "reproduced" / "stage_06_asd_001r_full_checkpoint"
EXPECTED_ACCURACY = {"0.02": 0.9244, "0.05": 0.9554, "0.10": 0.9630, "0.20": 0.9630}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def load_protocol():
    spec = importlib.util.spec_from_file_location("asd_001r_frozen_protocol", PROTOCOL_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_task(task):
    """Top-level worker bezpieczny dla mechanizmu spawn w Windows."""
    return load_protocol().fit_pilot_task(task)


def verify_frozen_inputs():
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    actual_protocol = sha256_file(PROTOCOL_FILE)
    if actual_protocol != lock["protocol_sha256"]:
        raise RuntimeError(
            "Kod protokołu różni się od zamrożonej wersji. Pełny bieg zatrzymano."
        )
    provenance = json.loads(PROVENANCE_FILE.read_text(encoding="utf-8"))
    historical_text = HISTORICAL_FILE.read_text(encoding="utf-8").rstrip("\n")
    actual_historical = sha256_bytes(historical_text.encode())
    if actual_historical != provenance["historical_source_sha256"]:
        raise RuntimeError(
            "Historyczne źródło ASD-001 uległo zmianie. Pełny bieg zatrzymano."
        )
    return lock, actual_historical


def atomic_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def task_key(c_value, seed):
    return f"C={c_value:.2f}|seed={seed:02d}"


def configuration(lock, historical_hash):
    return {
        "experiment_id": "ASD-001R",
        "execution_mode": "FULL_CONFIRMATORY_SUPPLEMENT",
        "protocol_id": lock["protocol_id"],
        "protocol_sha256": lock["protocol_sha256"],
        "historical_source_sha256": historical_hash,
        "c_values": lock["confirmation_c_values"],
        "seeds": lock["confirmation_seeds"],
        "random_candidates": lock["random_candidates"],
        "max_iter": lock["max_iter"],
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
            "Istniejący checkpoint FULL ma inną konfigurację i nie został nadpisany."
        )
    return payload


def ranks_are(item, expected):
    values = list(item["true_ranks"].values())
    return all(value is not None for value in values) and sorted(values) == expected


def task_pass(item):
    ablation = item["oracle_ablation"]["accuracy"]
    return (
        ranks_are(item, [1, 2])
        and min(item["true_importances"].values()) > 1e-10
        and item["min_true_margin_over_best_random"] > 0.0
        and "ConvergenceWarning" not in item["warning_types"]
        and ablation["combined_gain"] > 0.0
    )


def aggregate(tasks, c_values, seeds):
    rows = {}
    for c_value in c_values:
        selected = [tasks[task_key(c_value, seed)] for seed in seeds]
        normalized_ranks = []
        for item in selected:
            unresolved_rank = len(item["candidate_order"]) + 1
            normalized_ranks.append(
                [
                    rank if rank is not None else unresolved_rank
                    for rank in item["true_ranks"].values()
                ]
            )
        best_ranks = [min(values) for values in normalized_ranks]
        worst_ranks = [max(values) for values in normalized_ranks]
        rows[f"{c_value:.2f}"] = {
            "fits": len(selected),
            "structural_passes": sum(task_pass(item) for item in selected),
            "accuracy": float(np.mean([item["accuracy"] for item in selected])),
            "top1_true": sum(
                item["top_candidates"] and item["top_candidates"][0] in {
                    "flip_horizontal", "rotate_180"
                }
                for item in selected
            ),
            "both_true_top10": sum(
                all(
                    item["true_ranks"][name] is not None
                    and item["true_ranks"][name] <= 10
                    for name in ("flip_horizontal", "rotate_180")
                )
                for item in selected
            ),
            "both_true_top2": sum(ranks_are(item, [1, 2]) for item in selected),
            "mean_best_rank": float(np.mean(best_ranks)),
            "mean_worst_rank": float(np.mean(worst_ranks)),
            "positive_true_importances": sum(
                min(item["true_importances"].values()) > 1e-10 for item in selected
            ),
            "positive_margin_over_random": sum(
                item["min_true_margin_over_best_random"] > 0.0 for item in selected
            ),
            "minimum_margin_over_random": float(
                min(item["min_true_margin_over_best_random"] for item in selected)
            ),
            "positive_combined_ablation_gain": sum(
                item["oracle_ablation"]["accuracy"]["combined_gain"] > 0.0
                for item in selected
            ),
            "mean_combined_ablation_gain": float(
                np.mean(
                    [
                        item["oracle_ablation"]["accuracy"]["combined_gain"]
                        for item in selected
                    ]
                )
            ),
            "convergence_warnings": sum(
                "ConvergenceWarning" in item["warning_types"] for item in selected
            ),
        }
    return rows


def compare_with_publication(rows, tasks, expected_fits):
    structural = all(
        row["fits"] == 10
        and row["structural_passes"] == 10
        and row["top1_true"] == 10
        and row["both_true_top10"] == 10
        and row["both_true_top2"] == 10
        and row["mean_best_rank"] == 1.0
        and row["mean_worst_rank"] == 2.0
        and row["positive_true_importances"] == 10
        and row["positive_margin_over_random"] == 10
        and row["positive_combined_ablation_gain"] == 10
        and row["convergence_warnings"] == 0
        for row in rows.values()
    )
    deltas = {
        key: abs(row["accuracy"] - EXPECTED_ACCURACY[key])
        for key, row in rows.items()
    }
    max_delta = max(deltas.values())
    completed = len(tasks) == expected_fits
    if completed and structural:
        grade = "STRUCTURAL_RECONSTRUCTION_CONFIRMED"
    elif completed and any(row["structural_passes"] for row in rows.values()):
        grade = "STRUCTURAL_RECONSTRUCTION_PARTIAL"
    else:
        grade = "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED"
    return {
        "grade": grade,
        "completed_fits": len(tasks),
        "expected_fits": expected_fits,
        "publication_thesis_supported": completed and structural,
        "table_structure_reproduced": completed and structural,
        "historical_exact_reproduction": False,
        "numeric_accuracy_deltas": deltas,
        "max_numeric_accuracy_delta": max_delta,
        "numeric_comparison": (
            "CLOSE_AFTER_CORRECTION" if max_delta <= 0.002 else "DIFFERENCE_AFTER_CORRECTION"
        ),
        "interpretation": (
            "This is a supplementary test of a frozen corrected generator. "
            "It cannot identify the unpublished historical code version."
        ),
    }


def manifest(directory):
    target = directory / "MANIFEST_SHA256.txt"
    lines = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path != target:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(directory).as_posix()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output, payload):
    comparison = payload["comparison"]
    lines = [
        "# ASD-001R FULL — raport eksperymentu uzupełniającego",
        "",
        f"**Werdykt: {comparison['grade']}.**",
        "",
        "Eksperyment używa zamrożonego, jawnie poprawionego generatora dwóch",
        "symetrii. Nie jest historycznym `EXACT_MATCH` i nie zastępuje ASD-001.",
        "",
        "| C | Accuracy | Tabela | Delta | Top1 True | Obie Top10 | Obie Top2 | Śr. best | Śr. worst | Min. margines |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c_value, row in payload["summary_by_c"].items():
        lines.append(
            f"| {c_value} | {row['accuracy']:.4f} | {EXPECTED_ACCURACY[c_value]:.4f} | "
            f"{comparison['numeric_accuracy_deltas'][c_value]:.4f} | "
            f"{row['top1_true']}/10 | {row['both_true_top10']}/10 | "
            f"{row['both_true_top2']}/10 | {row['mean_best_rank']:.1f} | "
            f"{row['mean_worst_rank']:.1f} | {row['minimum_margin_over_random']:.4f} |"
        )
    lines += [
        "",
        "## Interpretacja",
        "",
        "Potwierdzenie strukturalne oznacza, że dwie symetrie rzeczywiście użyte",
        "do generowania etykiet są autonomicznie identyfikowane wśród 99",
        "kandydatów zgodnie ze strukturą rang tabeli 4.2.",
        "",
        "Różnice dokładności są raportowane oddzielnie i nie mogą być ukryte.",
        "Pełne dane każdego dopasowania znajdują się w `results.json`.",
    ]
    (output / "REPORT_PL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize(checkpoint, config, session_seconds):
    tasks = checkpoint["tasks"]
    c_values = config["c_values"]
    seeds = config["seeds"]
    rows = aggregate(tasks, c_values, seeds)
    expected_fits = len(c_values) * len(seeds)
    comparison = compare_with_publication(rows, tasks, expected_fits)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "reproduced" / "stage_06_asd_001r_full" / stamp
    output.mkdir(parents=True, exist_ok=True)
    warning_counts = {}
    for item in tasks.values():
        for warning_name in item["warning_types"]:
            warning_counts[warning_name] = warning_counts.get(warning_name, 0) + 1
    payload = {
        "experiment_id": "ASD-001R",
        "relationship_to_original": "PARALLEL_SUPPLEMENTARY_EXPERIMENT",
        "execution_mode": "FULL_CONFIRMATORY_SUPPLEMENT",
        "run_utc": now.isoformat(),
        "configuration": config,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "processor_count": os.cpu_count(),
        },
        "comparison": comparison,
        "summary_by_c": rows,
        "warning_counts": warning_counts,
        "tasks": tasks,
        "accumulated_fit_seconds": round(
            sum(item["duration_seconds"] for item in tasks.values()), 6
        ),
        "current_session_seconds": round(session_seconds, 6),
    }
    atomic_json(output / "results.json", payload)
    write_report(output, payload)
    manifest(output)
    latest = ROOT / "reproduced" / "stage_06_asd_001r_full" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    artifact = ROOT / "artifacts" / f"BOHN_ORIGINAL_STAGE_06_ASD_001R_FULL_{stamp}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    zip_path = Path(shutil.make_archive(str(artifact), "zip", root_dir=output))
    return output, zip_path, payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 2:
        parser.error("--workers musi wynosić 1 lub 2")

    lock, historical_hash = verify_frozen_inputs()
    config = configuration(lock, historical_hash)
    if args.dry_run:
        print("ASD-001R FULL PROTOCOL LOCK: PASS")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0

    c_values = config["c_values"]
    seeds = config["seeds"]
    random_count = config["random_candidates"]
    max_iter = config["max_iter"]
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
    print(f"ASD-001R FULL: checkpoint {len(tasks)}/{len(all_tasks)}", flush=True)
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
                        f"ASD-001R FULL: nadal działa | checkpoint "
                        f"{len(tasks)}/{len(all_tasks)} | {elapsed:.0f} s",
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
                        f"ASD-001R FULL: {key} | {label} | checkpoint "
                        f"{len(tasks)}/{len(all_tasks)} | {item['duration_seconds']:.1f} s",
                        flush=True,
                    )
        except KeyboardInterrupt:
            for future in pending:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            print("ASD-001R FULL: przerwano; checkpointy pozostają zachowane.", flush=True)
            return 130
        finally:
            if not getattr(executor, "_shutdown_thread", False):
                executor.shutdown(wait=True, cancel_futures=False)

    output, zip_path, payload = finalize(
        checkpoint, config, time.perf_counter() - started
    )
    comparison = payload["comparison"]
    print(f"ASD-001R FULL: {comparison['grade']}")
    print(
        f"FITS: {comparison['completed_fits']}/{comparison['expected_fits']} | "
        f"NUMERIC: {comparison['numeric_comparison']}"
    )
    print(f"RESULTS: {output}")
    print(f"ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
