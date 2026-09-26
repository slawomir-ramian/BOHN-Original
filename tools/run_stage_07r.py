#!/usr/bin/env python3
"""Runner pilota i pełnego potwierdzenia pięciu rekonstrukcji Etapu 07R."""
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
BASE = ROOT / "experiments" / "05_permutation_and_representation_supplementary"
IDS = ["PL-002R", "PL-003R", "HD-003R", "CMP-001R", "CMP-002R"]
LOCK = BASE / "STAGE_07R_PROTOCOL_LOCK.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_lock() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in lock["files"].items():
        path = ROOT / relative
        actual = sha(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({"file": relative, "expected": expected, "actual": actual})
    if mismatches:
        raise RuntimeError("PROTOCOL LOCK MISMATCH: " + json.dumps(mismatches, ensure_ascii=False))
    return lock


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_unit(experiment_id: str, mode: str, raw: Path) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    result_path = raw / f"{experiment_id}_result.json"
    command = [sys.executable, "-u", str(ROOT / "tools" / "run_stage_07r_unit.py"), "--id", experiment_id, "--mode", mode, "--result", str(result_path)]
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    start = time.perf_counter()
    timed_out = False
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, text=True, encoding="utf-8", errors="replace", stdout=stdout, stderr=stderr)
        heartbeat = start
        while process.poll() is None:
            now = time.perf_counter()
            if now - heartbeat >= 60:
                print(f"{experiment_id}: nadal działa | {now - start:.0f} s", flush=True)
                heartbeat = now
            if now - start >= 14400:
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
            stderr.write("\n[RUNNER_TIMEOUT] Przekroczono 14400 s.\n")
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    payload = json.loads(result_path.read_text(encoding="utf-8")) if return_code == 0 and result_path.is_file() else None
    return {
        "execution_status": "TIMEOUT" if timed_out else ("PASS" if return_code == 0 else "FAILED"),
        "return_code": return_code,
        "duration_seconds": round(time.perf_counter() - start, 6),
        "result": payload,
        "stdout_file": f"raw/{experiment_id}_stdout.txt",
        "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "result_file": f"raw/{experiment_id}_result.json" if result_path.is_file() else None,
        "stdout_sha256": digest(stdout_text.encode()),
        "stderr_sha256": digest(stderr_text.encode()),
        "stderr_nonempty": bool(stderr_text.strip()),
    }


def manifest(output: Path) -> None:
    path = output / "MANIFEST_SHA256.txt"
    rows = []
    for file in sorted(output.rglob("*")):
        if file.is_file() and file != path:
            rows.append(f"{sha(file)}  {file.relative_to(output).as_posix()}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def report(payload: dict) -> str:
    lines = ["# Etap 07R — raport rekonstrukcji uzupełniających", "", f"- Tryb: `{payload['mode']}`", f"- Grade: `{payload['grade']}`", "- Relacja do PDF: `OUTSIDE_115_PDF_CHRONOLOGY`", "", "| # | ID | Wykonanie | Status naukowy | Kryterium | Czas [s] |", "|---:|---|---|---|---|---:|"]
    for index, experiment_id in enumerate(payload["source_order"], 1):
        row = payload["experiments"][experiment_id]
        result = row.get("result") or {}
        lines.append(f"| {index} | {experiment_id} | {row['execution_status']} | {result.get('status', 'NO_RESULT')} | {result.get('primary_criterion_pass', '')} | {row['duration_seconds']:.2f} |")
    lines += ["", "Rekonstrukcje nie zastępują pięciu jednostek `NARRATIVE_ONLY` i nie są przedstawiane jako odzyskany kod historyczny. Dokładne dopasowanie wartości tabelarycznych ma status wtórny."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pilot", "full"], default="full")
    parser.add_argument("--only", choices=IDS)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-lock", action="store_true")
    args = parser.parse_args()
    lock = validate_lock()
    if args.validate_lock:
        print(f"PROTOCOL LOCK PASS: {lock['protocol_id']}")
        return 0
    selected = [args.only] if args.only else IDS
    mode = "only" if args.only else args.mode
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    family = "stage_07r_full" if args.mode == "full" else "stage_07r_pilot"
    output = args.output_dir or ROOT / "reproduced" / family / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        row = run_unit(experiment_id, args.mode, raw)
        results[experiment_id] = row
        scientific = (row.get("result") or {}).get("status", "NO_RESULT")
        print(f"{experiment_id}: {row['execution_status']} | {scientific} | {row['duration_seconds']:.2f} s", flush=True)
        checkpoint = {"stage": "07R", "mode": mode, "run_utc": now.isoformat(), "completed_units": list(results), "experiments": results}
        (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    execution_pass = all(row["execution_status"] == "PASS" for row in results.values())
    criteria = [(row.get("result") or {}).get("primary_criterion_pass") for row in results.values()]
    if args.mode == "pilot":
        grade = "STRUCTURAL_PILOT_PASS" if execution_pass else "PILOT_EXECUTION_FAILED"
    elif execution_pass and all(value is True for value in criteria):
        grade = "SUPPLEMENTARY_RECONSTRUCTIONS_CONFIRMED"
    elif execution_pass and any(value is True for value in criteria):
        grade = "PARTIAL_SUPPLEMENTARY_CONFIRMATION"
    elif execution_pass:
        grade = "SUPPLEMENTARY_RECONSTRUCTIONS_NOT_CONFIRMED"
    else:
        grade = "EXECUTION_FAILED"
    versions = {}
    for module, key in (("numpy", "numpy"), ("pandas", "pandas"), ("sklearn", "scikit_learn")):
        try:
            versions[key] = __import__(module).__version__
        except ImportError:
            versions[key] = None
    payload = {"stage": "07R", "mode": mode, "run_utc": now.isoformat(), "source_order": selected, "full_source_order": IDS, "grade": grade, "protocol_lock": lock, "environment": {"python": sys.version, "platform": platform.platform(), **versions, "processor_count": os.cpu_count()}, "experiments": results}
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "RECONSTRUCTION_REPORT_PL.md").write_text(report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / family / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text((str(output.relative_to(ROOT)).replace("\\", "/") if output.is_relative_to(ROOT) else str(output)) + "\n", encoding="utf-8")
    manifest(output)
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    label = "PILOT" if args.mode == "pilot" else "FULL"
    archive = Path(shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_07R_{label}_{stamp}"), "zip", root_dir=output))
    print(f"GRADE: {grade}")
    print(f"RESULTS: {output}")
    print(f"ZIP: {archive}")
    return 0 if execution_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
