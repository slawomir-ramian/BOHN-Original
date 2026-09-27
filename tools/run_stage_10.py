#!/usr/bin/env python3
"""Uruchom Etap 10 w kolejności PDF-a, z checkpointem i heartbeat."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "08_meta_sbohn"
SOURCE_CHRONOLOGY = [f"MS-{number:03d}" for number in range(1, 11)]
SMOKE = ["MS-001", "MS-005", "MS-009", "MS-010"]
AUDITED_ONLY = set(SOURCE_CHRONOLOGY[:8])
SOURCE_FRAGMENT = {"MS-005", "MS-006", "MS-007", "MS-008"}
SHARED_OWNER = {"MS-010": "MS-009"}
PUBLISHED = {
    "MS-009": {
        ("accuracy_only", "easy", "final_acc"): 0.9104,
        ("fixed_geometry", "easy", "final_acc"): 0.9057,
        ("accuracy_only", "medium", "final_acc"): 0.8894,
        ("fixed_geometry", "medium", "final_acc"): 0.8897,
        ("accuracy_only", "hard", "final_acc"): 0.8882,
        ("fixed_geometry", "hard", "final_acc"): 0.8940,
    },
    "MS-010": {
        ("accuracy_only", "easy", "final_acc"): 0.9104,
        ("fixed_geometry", "easy", "final_acc"): 0.9057,
        ("annealed_geometry", "easy", "final_acc"): 0.9226,
        ("accuracy_only", "medium", "final_acc"): 0.8894,
        ("fixed_geometry", "medium", "final_acc"): 0.8897,
        ("annealed_geometry", "medium", "final_acc"): 0.8902,
        ("accuracy_only", "hard", "final_acc"): 0.8882,
        ("fixed_geometry", "hard", "final_acc"): 0.8940,
        ("annealed_geometry", "hard", "final_acc"): 0.8929,
        ("accuracy_only", "easy", "best_task_sim"): 0.1086,
        ("fixed_geometry", "easy", "best_task_sim"): 0.0992,
        ("annealed_geometry", "easy", "best_task_sim"): 0.1250,
        ("accuracy_only", "medium", "best_task_sim"): 0.0688,
        ("fixed_geometry", "medium", "best_task_sim"): 0.0828,
        ("annealed_geometry", "medium", "best_task_sim"): 0.1164,
        ("accuracy_only", "hard", "best_task_sim"): 0.0531,
        ("fixed_geometry", "hard", "best_task_sim"): 0.0672,
        ("annealed_geometry", "hard", "best_task_sim"): 0.0930,
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def close_status(conclusion: bool, deltas: list[float], tolerance: float) -> str:
    if conclusion and deltas and max(deltas) <= tolerance:
        return "CLOSE_NUMERIC_MATCH"
    if conclusion:
        return "CONCLUSION_MATCH"
    return "NUMERIC_DIFFERENCE"


def comparison(experiment_id: str, result_data: dict) -> dict:
    try:
        summary = result_data["summary"]
        published = PUBLISHED[experiment_id]
        deltas = [abs(float(summary[mode][task][metric]) - value) for (mode, task, metric), value in published.items()]
        if experiment_id == "MS-009":
            hard = summary["fixed_geometry"]["hard"]["final_acc"] > summary["accuracy_only"]["hard"]["final_acc"]
            medium = summary["fixed_geometry"]["medium"]["final_acc"] >= summary["accuracy_only"]["medium"]["final_acc"] - 0.005
            conclusion = bool(hard and medium)
            tolerance = 0.03
            note = "Kontrola stałej regularyzacji geometrii: korzyść na trudnym zadaniu i brak materialnej straty na średnim."
        elif experiment_id == "MS-010":
            similarity = all(
                summary["annealed_geometry"][task]["best_task_sim"] > summary["accuracy_only"][task]["best_task_sim"]
                for task in ("easy", "medium", "hard")
            )
            medium_basin = summary["annealed_geometry"]["medium"]["acc092_and_sim025"] > summary["accuracy_only"]["medium"]["acc092_and_sim025"]
            hard_basin = summary["annealed_geometry"]["hard"]["acc092_and_sim025"] > summary["accuracy_only"]["hard"]["acc092_and_sim025"]
            conclusion = bool(similarity and medium_basin and hard_basin)
            tolerance = 0.05
            note = "Kontrola annealingu: wzrost podobieństwa na trzech zadaniach oraz częstsze wejście do geometrycznych basinów."
        else:
            raise ValueError(experiment_id)
        return {
            "status": close_status(conclusion, deltas, tolerance),
            "scientific_conclusion_preserved": conclusion,
            "max_reported_numeric_delta": max(deltas),
            "actual_summary": summary,
            "note": note,
        }
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return {
            "status": "UNPARSEABLE_OUTPUT", "scientific_conclusion_preserved": False,
            "max_reported_numeric_delta": None, "actual_summary": {}, "note": str(exc),
        }


def source_path(experiment_id: str) -> Path:
    return BASE / experiment_id / "historical" / "source_from_monograph.py"


def audited_result(experiment_id: str, raw: Path) -> dict:
    provenance = json.loads((BASE / experiment_id / "provenance.json").read_text(encoding="utf-8"))
    source = BASE / experiment_id / "historical" / provenance["reported_result_file"]
    text = source.read_text(encoding="utf-8").rstrip("\n")
    if digest(text.encode()) != provenance["reported_result_sha256"]:
        raise RuntimeError(f"Niezgodny hash wyniku {experiment_id}")
    stdout = raw / f"{experiment_id}_stdout.txt"
    stderr = raw / f"{experiment_id}_stderr.txt"
    stdout.write_text("AUDITED_REPORTED_RESULT\n" + text + "\n", encoding="utf-8", newline="\n")
    stderr.write_text("", encoding="utf-8")
    boundary = "SOURCE_FRAGMENT_ONLY" if experiment_id in SOURCE_FRAGMENT else "NARRATIVE_ONLY"
    return {
        "execution_status": "PASS", "return_code": 0, "duration_seconds": 0.0,
        "execution_mode": "AUDITED_REPORTED_RESULT", "source_boundary": boundary,
        "executed_file": str(source.relative_to(ROOT)).replace("\\", "/"),
        "stdout_sha256": digest(stdout.read_bytes()), "stderr_sha256": digest(b""),
        "stderr_nonempty": False, "stdout_file": f"raw/{experiment_id}_stdout.txt",
        "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "comparison": {
            "status": "AUDITED_REPORTED_RESULT", "scientific_conclusion_preserved": None,
            "max_reported_numeric_delta": None, "actual_summary": {},
            "note": "Zachowano dokładny wynik źródłowy bez przedstawiania brakującego programu jako kodu historycznego.",
        },
    }


def run_process(experiment_id: str, raw: Path, smoke: bool = False) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    if smoke:
        smoke_path = ROOT / "tools" / "smoke_stage_10.py"
        args = [sys.executable, str(smoke_path), "--only", experiment_id]
        executed = str(smoke_path.relative_to(ROOT)).replace("\\", "/")
    else:
        source = source_path(experiment_id)
        wrapper = ROOT / "tools" / "execute_historical_stage_10.py"
        checkpoint = ROOT / "reproduced" / "stage_10_checkpoint"
        args = [sys.executable, "-u", str(wrapper), str(source), "--run-dir", str(checkpoint)]
        executed = str(source.relative_to(ROOT)).replace("\\", "/")
    start = time.perf_counter()
    timed_out = False
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(args, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", stdout=stdout, stderr=stderr)
        heartbeat = start
        while process.poll() is None:
            now = time.perf_counter()
            if now - heartbeat >= 60:
                if smoke:
                    suffix = ""
                else:
                    cells = ROOT / "reproduced" / "stage_10_checkpoint" / "cells"
                    count = len(list(cells.glob("*.json"))) if cells.exists() else 0
                    suffix = f" | checkpoint {count}/180"
                print(f"{experiment_id}: nadal działa | {now - start:.0f} s{suffix}", flush=True)
                heartbeat = now
            if now - start >= 86400:
                timed_out = True
                process.terminate()
                try:
                    process.wait(30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break
            time.sleep(1)
        return_code = process.returncode
        if timed_out:
            stderr.write("\n[RUNNER_TIMEOUT] Przekroczono 86400 s; checkpoint pozostaje do wznowienia.\n")
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    historical_json_file = None
    result_data = {}
    if not smoke and not timed_out and return_code == 0:
        checkpoint_root = ROOT / "reproduced" / "stage_10_checkpoint"
        generated = checkpoint_root / "meta_sbohn_results.json"
        if generated.exists():
            historical_json_file = raw / f"{experiment_id}_historical_result.json"
            shutil.copyfile(generated, historical_json_file)
            result_data = json.loads(historical_json_file.read_text(encoding="utf-8"))
            cell_logs = checkpoint_root / "cell_logs"
            if cell_logs.exists():
                shutil.copytree(cell_logs, raw / f"{experiment_id}_cell_logs", dirs_exist_ok=True)
    if timed_out:
        compare = {"status": "TIMEOUT", "scientific_conclusion_preserved": False, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Techniczny limit czasu; bieg można wznowić."}
    elif smoke:
        compare = {"status": "SMOKE_PROBE_PASS" if return_code == 0 else "SMOKE_PROBE_FAILED", "scientific_conclusion_preserved": None, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Smoke nie zastępuje pełnego programu."}
    elif return_code == 0:
        compare = comparison(experiment_id, result_data)
    else:
        compare = {"status": "EXECUTION_FAILED", "scientific_conclusion_preserved": False, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Historyczny program zakończył się błędem technicznym."}
    status = "TIMEOUT" if timed_out else ("PASS" if return_code == 0 else "FAILED")
    result = {
        "execution_status": status, "return_code": return_code,
        "duration_seconds": round(time.perf_counter() - start, 6),
        "execution_mode": "SMOKE_PROBE" if smoke else "HISTORICAL_SOURCE_ORCHESTRATED",
        "executed_file": executed, "stdout_sha256": digest(stdout_text.encode()),
        "stderr_sha256": digest(stderr_text.encode()), "stderr_nonempty": bool(stderr_text.strip()),
        "stdout_file": f"raw/{experiment_id}_stdout.txt", "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "comparison": compare,
    }
    if historical_json_file:
        result["historical_result_file"] = f"raw/{historical_json_file.name}"
        result["historical_result_sha256"] = digest(historical_json_file.read_bytes())
    return result


def reuse_shared(experiment_id: str, owner: str, raw: Path, owner_row: dict) -> dict:
    for suffix in ("stdout.txt", "stderr.txt", "historical_result.json"):
        source = raw / f"{owner}_{suffix}"
        target = raw / f"{experiment_id}_{suffix}"
        if source.exists():
            shutil.copyfile(source, target)
    result_json = raw / f"{experiment_id}_historical_result.json"
    result_data = json.loads(result_json.read_text(encoding="utf-8"))
    stdout = raw / f"{experiment_id}_stdout.txt"
    row = dict(owner_row)
    row.update({
        "duration_seconds": 0.0, "execution_mode": "HISTORICAL_SOURCE_SHARED_RUN",
        "executed_file": str(source_path(experiment_id).relative_to(ROOT)).replace("\\", "/"),
        "stdout_file": f"raw/{experiment_id}_stdout.txt", "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "historical_result_file": f"raw/{experiment_id}_historical_result.json",
        "stdout_sha256": digest(stdout.read_bytes()), "historical_result_sha256": digest(result_json.read_bytes()),
        "comparison": comparison(experiment_id, result_data),
    })
    return row


def make_manifest(output: Path) -> None:
    manifest = output / "MANIFEST_SHA256.txt"
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != manifest:
            rows.append(f"{digest(path.read_bytes())}  {path.relative_to(output).as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_report(payload: dict) -> str:
    lines = [
        "# Etap 10 — raport wykonania", "",
        "Jednostki wykonano w kolejności PDF-a. Status techniczny jest oddzielony od zgodności naukowej.", "",
        "| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_mode']} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += [
        "", "## Granica źródłowa", "",
        "Dwie jednostki dzielą kompletny program historyczny. Cztery jednostki curriculum mają jedynie fragment inicjalizacji populacji, a cztery pierwsze jednostki mają wyniki bez kodu docelowego.",
        "", "`NUMERIC_DIFFERENCE` opisuje wynik naukowy i nie jest błędem wykonania programu.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--only", choices=SOURCE_CHRONOLOGY)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.only:
        selected, mode, smoke = [args.only], "only", False
    elif args.smoke:
        selected, mode, smoke = SMOKE, "smoke", True
    else:
        selected, mode, smoke = SOURCE_CHRONOLOGY, "full", False
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or ROOT / "reproduced" / "stage_10_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if not smoke and experiment_id in AUDITED_ONLY:
            row = audited_result(experiment_id, raw)
        elif not smoke and experiment_id in SHARED_OWNER and SHARED_OWNER[experiment_id] in results:
            row = reuse_shared(experiment_id, SHARED_OWNER[experiment_id], raw, results[SHARED_OWNER[experiment_id]])
        else:
            row = run_process(experiment_id, raw, smoke)
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)
        checkpoint = {"stage": "10", "run_utc": now.isoformat(), "mode": mode, "source_chronology": selected, "completed_units": list(results), "experiments": results}
        (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    versions = {}
    for module, key in (("numpy", "numpy"), ("sklearn", "scikit_learn"), ("pandas", "pandas")):
        try:
            versions[key] = __import__(module).__version__
        except ImportError:
            versions[key] = None
    payload = {
        "stage": "10", "run_utc": now.isoformat(), "mode": mode,
        "source_chronology": selected, "full_source_chronology": SOURCE_CHRONOLOGY,
        "environment": {"python": sys.version, "platform": platform.platform(), **versions, "processor_count": os.cpu_count()},
        "source_boundary": {"executable_units": 2, "shared_programs": 1, "source_fragment_only": sorted(SOURCE_FRAGMENT), "narrative_only": SOURCE_CHRONOLOGY[:4]},
        "experiments": results,
    }
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(make_report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / "stage_10_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text((str(output.relative_to(ROOT)).replace("\\", "/") if output.is_relative_to(ROOT) else str(output)) + "\n", encoding="utf-8")
    make_manifest(output)
    archive = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = Path(shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_10_RESULTS_{stamp}"), "zip", root_dir=output))
    print(f"RESULTS: {output}")
    if archive:
        print(f"ZIP: {archive}")
    technical_failure = any(
        row["execution_status"] != "PASS" or row["comparison"]["status"] in {"UNPARSEABLE_OUTPUT", "EXECUTION_FAILED", "TIMEOUT", "SMOKE_PROBE_FAILED"}
        for row in results.values()
    )
    return 1 if technical_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
