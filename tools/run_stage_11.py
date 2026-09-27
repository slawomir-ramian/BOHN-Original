#!/usr/bin/env python3
"""Uruchom Etap 11 w kolejności PDF-a i oddziel rekonstrukcję od źródła."""
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
BASE = ROOT / "experiments" / "09_adaptation_and_continual"
IDS = ["AD-001", "AD-002", "AD-003", "CL-001", "CL-002"]
SMOKE = ["AD-001", "AD-002", "CL-001", "CL-002"]
GROUP = {"AD-001": "perm_head", "CL-001": "perm_head", "AD-002": "fewshot", "AD-003": "fewshot", "CL-002": "fewshot"}
PROTOCOL = "STAGE_11_RECONSTRUCTION_V1"

PUBLISHED_AD1 = {
    "10": [15.30, 11.00, 11.10, 29.00, 10.90, 35.10],
    "50": [20.00, 13.30, 11.10, 36.00, 5.80, 50.30],
    "100": [25.90, 13.30, 11.10, 46.70, 19.90, 53.60],
    "500": [51.40, 48.00, 8.40, 67.20, 38.00, 76.30],
    "2000": [57.90, 59.40, 9.50, 72.20, 60.10, 82.20],
    "5000": [64.70, 60.50, 9.20, 73.40, 64.20, 83.20],
}
AD1_KEYS = ["perm_head", "head_only", "perm_only", "full_tune", "mlp_head", "mlp_full"]
PUBLISHED_AD2 = {
    "10": [14.75, 21.03, 20.85, 18.81, 36.42, 41.06],
    "50": [19.40, 32.34, 42.45, 41.13, 55.95, 59.97],
    "100": [24.29, 47.57, 52.24, 53.10, 57.53, 62.25],
    "500": [25.19, 70.12, 74.40, 74.15, 76.50, 76.46],
}
AD2_KEYS = ["sbohn_perm_only", "sbohn_head_only", "sbohn_full_tune", "mlp_fine_tune", "cnn_fine_tune", "mlp_scratch"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numeric_deltas(rows: dict, published: dict, keys: list[str]) -> list[float]:
    return [abs(float(rows[shots][key]) - expected) for shots, values in published.items() for key, expected in zip(keys, values)]


def grade(conclusion: bool, deltas: list[float], tolerance: float) -> str:
    if conclusion and deltas and max(deltas) <= tolerance:
        return "CLOSE_NUMERIC_MATCH"
    if conclusion:
        return "CONCLUSION_MATCH"
    return "NUMERIC_DIFFERENCE"


def comparison(experiment_id: str, payload: dict) -> dict:
    try:
        if experiment_id == "AD-001":
            row = payload["fewshot"]["5000"]
            deltas = numeric_deltas(payload["fewshot"], PUBLISHED_AD1, AD1_KEYS)
            conclusion = row["perm_head"] > row["head_only"] and row["perm_only"] <= 15.0
            note = "Test komplementarności routingu i głowicy oraz zachowania perm-only blisko poziomu losowego."
            tolerance = 12.0
        elif experiment_id == "AD-002":
            rows = payload["fewshot"]
            deltas = numeric_deltas(rows, PUBLISHED_AD2, AD2_KEYS)
            conclusion = rows["500"]["sbohn_head_only"] > rows["10"]["sbohn_head_only"] and rows["500"]["sbohn_full_tune"] > rows["10"]["sbohn_full_tune"]
            note = "Test wzrostu jakości transferu wraz z liczbą przykładów."
            tolerance = 12.0
        elif experiment_id == "AD-003":
            row = payload["fewshot"]["500"]
            gap = row["sbohn_full_tune"] - row["sbohn_head_only"]
            deltas = [abs(row["sbohn_head_only"] - 70.12), abs(row["sbohn_full_tune"] - 74.40)]
            conclusion = row["sbohn_head_only"] >= 0.85 * row["sbohn_full_tune"] and abs(gap) <= 10.0
            note = "Test modularności: head-only zachowuje co najmniej 85% jakości full-tune przy 500 próbkach."
            tolerance = 10.0
        elif experiment_id == "CL-001":
            row = payload["continual"]
            deltas = [
                abs(row["sbohn_mnist_before"] - 69.60), abs(row["sbohn_fashion"] - 58.50),
                abs(row["sbohn_mnist_after_restore"] - 69.60), abs(row["mlp_mnist_before"] - 92.10),
                abs(row["mlp_fashion"] - 83.20), abs(row["mlp_mnist_after_fashion"] - 21.20),
            ]
            conclusion = abs(row["sbohn_mnist_degradation"]) <= 1e-9 and row["mlp_mnist_degradation"] > 0
            note = "Test dokładnego przywrócenia modułu zadaniowego oraz dodatniego zapominania sekwencyjnego MLP."
            tolerance = 15.0
        elif experiment_id == "CL-002":
            row = payload["continual"]
            deltas = [
                abs(row["sbohn_mnist_before"] - 89.52), abs(row["sbohn_fashion_perm_only"] - 29.07),
                abs(row["sbohn_mnist_after_restore"] - 89.52), abs(row["mlp_mnist_before"] - 89.99),
                abs(row["mlp_fashion"] - 72.19), abs(row["mlp_mnist_after_fashion"] - 65.85),
            ]
            conclusion = abs(row["sbohn_mnist_degradation"]) <= 1e-9 and row["mlp_mnist_degradation"] > 0
            note = "Test exact restore macierzy permutacji w większym modelu i kontroli zapominania MLP."
            tolerance = 15.0
        else:
            raise ValueError(experiment_id)
        return {
            "status": grade(bool(conclusion), deltas, tolerance),
            "scientific_conclusion_preserved": bool(conclusion),
            "max_reported_numeric_delta_pp": max(deltas),
            "note": note,
        }
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return {"status": "UNPARSEABLE_OUTPUT", "scientific_conclusion_preserved": False, "max_reported_numeric_delta_pp": None, "note": str(exc)}


def run_probe(experiment_id: str, raw: Path) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    args = [sys.executable, str(ROOT / "tools" / "smoke_stage_11.py"), "--only", experiment_id]
    started = time.perf_counter()
    completed = subprocess.run(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
    return {
        "execution_status": "PASS" if completed.returncode == 0 else "FAILED",
        "return_code": completed.returncode,
        "duration_seconds": round(time.perf_counter() - started, 6),
        "execution_mode": "SMOKE_PROBE",
        "source_boundary": "SOURCE_FRAGMENT_ONLY",
        "stdout_file": f"raw/{stdout_path.name}", "stderr_file": f"raw/{stderr_path.name}",
        "stdout_sha256": digest(stdout_path.read_bytes()), "stderr_sha256": digest(stderr_path.read_bytes()),
        "comparison": {"status": "SMOKE_PROBE_PASS" if completed.returncode == 0 else "SMOKE_PROBE_FAILED", "scientific_conclusion_preserved": None, "max_reported_numeric_delta_pp": None, "note": "Sonda nie zastępuje pełnej rekonstrukcji."},
    }


def valid_checkpoint(path: Path, group: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload["protocol"] == PROTOCOL and payload["shared_listing"] == (58 if group == "perm_head" else 59)
    except (OSError, KeyError, ValueError, TypeError):
        return False


def execute_group(group: str, raw: Path) -> tuple[dict, float, int, str, str]:
    checkpoint_root = ROOT / "reproduced" / "stage_11_checkpoint"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    checkpoint = checkpoint_root / f"{group}.json"
    stdout_path = raw / f"_{group}_stdout.txt"
    stderr_path = raw / f"_{group}_stderr.txt"
    if valid_checkpoint(checkpoint, group):
        shutil.copyfile(checkpoint, raw / f"_{group}_result.json")
        stdout_path.write_text("CHECKPOINT REUSED\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return json.loads(checkpoint.read_text(encoding="utf-8")), 0.0, 0, stdout_path.name, stderr_path.name

    args = [sys.executable, "-u", str(ROOT / "tools" / "reconstruct_stage_11.py"), "--protocol", group, "--output", str(checkpoint)]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started = time.perf_counter()
    timed_out = False
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(args, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", stdout=stdout, stderr=stderr)
        heartbeat = started
        while process.poll() is None:
            now = time.perf_counter()
            if now - heartbeat >= 60:
                print(f"{group}: nadal działa | {now - started:.0f} s", flush=True)
                heartbeat = now
            if now - started >= 21600:
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
        return_code = 124
    if return_code != 0 or not valid_checkpoint(checkpoint, group):
        return {}, time.perf_counter() - started, return_code, stdout_path.name, stderr_path.name
    shutil.copyfile(checkpoint, raw / f"_{group}_result.json")
    return json.loads(checkpoint.read_text(encoding="utf-8")), time.perf_counter() - started, 0, stdout_path.name, stderr_path.name


def unit_from_group(experiment_id: str, payload: dict, duration: float, return_code: int,
                    group_stdout: Path, group_stderr: Path, raw: Path, shared: bool) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    shutil.copyfile(group_stdout, stdout_path)
    shutil.copyfile(group_stderr, stderr_path)
    result_path = raw / f"{experiment_id}_reconstruction_result.json"
    if payload:
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compare = comparison(experiment_id, payload) if return_code == 0 else {
        "status": "EXECUTION_FAILED", "scientific_conclusion_preserved": False,
        "max_reported_numeric_delta_pp": None, "note": "Rekonstrukcja zakończyła się błędem technicznym."
    }
    row = {
        "execution_status": "PASS" if return_code == 0 else "FAILED",
        "return_code": return_code,
        "duration_seconds": 0.0 if shared else round(duration, 6),
        "execution_mode": "RECONSTRUCTION_FROM_PUBLISHED_FRAGMENT_SHARED" if shared else "RECONSTRUCTION_FROM_PUBLISHED_FRAGMENT",
        "source_boundary": "SOURCE_FRAGMENT_ONLY",
        "historical_code_modified": False,
        "reconstruction_is_historical_source": False,
        "stdout_file": f"raw/{stdout_path.name}", "stderr_file": f"raw/{stderr_path.name}",
        "stdout_sha256": digest(stdout_path.read_bytes()), "stderr_sha256": digest(stderr_path.read_bytes()),
        "stderr_nonempty": bool(stderr_path.read_text(encoding="utf-8", errors="replace").strip()),
        "comparison": compare,
    }
    if result_path.exists():
        row["reconstruction_result_file"] = f"raw/{result_path.name}"
        row["reconstruction_result_sha256"] = digest(result_path.read_bytes())
    return row


def make_manifest(output: Path) -> None:
    manifest = output / "MANIFEST_SHA256.txt"
    rows = [f"{digest(path.read_bytes())}  {path.relative_to(output).as_posix()}" for path in sorted(output.rglob("*")) if path.is_file() and path != manifest]
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_report(payload: dict) -> str:
    lines = [
        "# Etap 11 — raport wykonania", "",
        "Pozycje 83–87 wykonano w kolejności PDF-a. Historyczne fragmenty nie zostały zmodyfikowane; brakujące fazy są jawną rekonstrukcją.", "",
        "| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_mode']} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += [
        "", "## Granica źródłowa", "",
        "Listingi 58 i 59 kończą fazy eksperymentalne komentarzami zamiast pełnej implementacji. Dlatego wynik nie może otrzymać statusu historycznego `EXACT_MATCH`; klasyfikacja dotyczy jawnej rekonstrukcji protokołu.",
        "", "`NUMERIC_DIFFERENCE` opisuje zgodność naukową, a nie awarię programu.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--only", choices=IDS)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.only:
        selected, mode, smoke = [args.only], "only", False
    elif args.smoke:
        selected, mode, smoke = SMOKE, "smoke", True
    else:
        selected, mode, smoke = IDS, "full", False
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or ROOT / "reproduced" / "stage_11_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    group_cache = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if smoke:
            row = run_probe(experiment_id, raw)
        else:
            group = GROUP[experiment_id]
            shared = group in group_cache
            if not shared:
                payload, duration, code, stdout_name, stderr_name = execute_group(group, raw)
                group_cache[group] = (payload, duration, code, stdout_name, stderr_name)
            payload, duration, code, stdout_name, stderr_name = group_cache[group]
            row = unit_from_group(experiment_id, payload, duration, code, raw / stdout_name, raw / stderr_name, raw, shared)
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)

    result_payload = {
        "stage": "11", "run_utc": now.isoformat(), "mode": mode,
        "source_chronology": selected, "experiments": results,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }
    (output / "results.json").write_text(json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(make_report(result_payload), encoding="utf-8")
    make_manifest(output)
    latest = ROOT / "reproduced" / "stage_11_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    print(f"RESULTS: {output}")
    if not smoke and not args.only:
        artifact = ROOT / "artifacts" / f"BOHN_ORIGINAL_STAGE_11_RESULTS_{stamp}.zip"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        if artifact.exists():
            artifact.unlink()
        shutil.make_archive(str(artifact.with_suffix("")), "zip", output)
        print(f"ZIP: {artifact}")
    return 0 if all(row["execution_status"] == "PASS" for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
