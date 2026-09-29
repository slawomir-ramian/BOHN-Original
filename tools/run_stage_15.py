#!/usr/bin/env python3
"""Runner Etapu 15: siedem jednostek z pełnego wspólnego listingu 71."""
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
IDS = ["RF-001", "RF-002", "MF-001", "MF-002", "MF-003", "MF-004", "MF-005"]
SMOKE = ["RF-001", "RF-002", "MF-001", "MF-003", "MF-005"]
PROGRAM_BY_ID = {"RF-001": "v1", "RF-002": "testA", "MF-001": "v2", "MF-002": "v2",
                 "MF-003": "v3", "MF-004": "v4", "MF-005": "v5"}
REFERENCE_V1 = {"RAW": .491, "BOHN": .803, "FBOHN": .989, "FBOHN_SRL_12": .871}
REFERENCE_TEST_A = {
    0.0: {"RAW": .550, "BOHN": .605, "FBOHN": .622},
    0.1: {"RAW": .545, "BOHN": .600, "FBOHN": .626},
    0.3: {"RAW": .543, "BOHN": .589, "FBOHN": .615},
    0.5: {"RAW": .539, "BOHN": .584, "FBOHN": .609},
}
REFERENCE_V5 = {"Meta-FBOHN-v5-library": .6528, "Meta-FBOHN-v4-single": .6449,
                "FBOHN": .6182, "FBOHN-poly-control": .6249}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def summary_map(payload: dict) -> dict:
    result = {}
    for row in payload["summary"]:
        key = (float(row["noise"]), row["representation"]) if "noise" in row else row["representation"]
        result[key] = float(row["acc_mean"])
    return result


def compare_v1(payload: dict) -> dict:
    values = summary_map(payload)
    maximum = max(abs(values[name] - target) for name, target in REFERENCE_V1.items())
    conclusion = values["FBOHN"] > values["FBOHN_SRL_12"] > values["BOHN"] > values["RAW"]
    return classification(conclusion, maximum, "FBOHN zachowuje pełną strukturę i wygrywa z BOHN, RAW oraz SRL-12.")


def compare_test_a(payload: dict) -> dict:
    values = summary_map(payload)
    maximum = max(abs(values[(noise, name)] - target)
                  for noise, row in REFERENCE_TEST_A.items() for name, target in row.items())
    conclusion = all(values[(noise, "FBOHN")] > values[(noise, "BOHN")] > values[(noise, "RAW")]
                     for noise in REFERENCE_TEST_A)
    return classification(conclusion, maximum, "FBOHN zachowuje przewagę poza przestrzenią reprezentacji.")


def compare_v2(payload: dict, experiment_id: str) -> dict:
    values = summary_map(payload)
    name = "Meta-FBOHN-v1-global" if experiment_id == "MF-001" else "Meta-FBOHN-v2-orbitwise"
    maximum = max(abs(values[(noise, name)] - values[(noise, "FBOHN")]) for noise in REFERENCE_TEST_A)
    conclusion = maximum <= 1e-9
    result = classification(conclusion, maximum, "Dodatnie skalowanie jest kasowane przez StandardScaler; wynik negatywny odtworzony.")
    result["comparison_to_fbohn"] = name
    return result


def compare_v3(payload: dict) -> dict:
    values = summary_map(payload)
    improvements = [values[(noise, "Meta-FBOHN-v3-mixing")] - values[(noise, "FBOHN")]
                    for noise in REFERENCE_TEST_A]
    conclusion = sum(improvements) / len(improvements) > 0
    result = classification(conclusion, None, "Learned Orbit Mixing daje dodatnią średnią zmianę względem FBOHN.")
    result["mean_improvement_pp"] = 100 * sum(improvements) / len(improvements)
    return result


def compare_v4(payload: dict) -> dict:
    values = summary_map(payload)
    improvements = [values[(noise, "Meta-FBOHN-v4-single")] - values[(noise, "FBOHN")]
                    for noise in REFERENCE_TEST_A]
    dimensions = {int(round(row["feature_dim"])) for row in payload["summary"]
                  if row["representation"] == "Meta-FBOHN-v4-single"}
    conclusion = sum(improvements) / len(improvements) > 0 and dimensions == {46}
    result = classification(conclusion, None, "Symboliczny kompozytor dodaje 16 relacji i poprawia średni wynik.")
    result["mean_improvement_pp"] = 100 * sum(improvements) / len(improvements)
    return result


def compare_v5(payload: dict) -> dict:
    values = summary_map(payload)
    averages = {name: sum(values[(noise, name)] for noise in REFERENCE_TEST_A) / 4
                for name in REFERENCE_V5}
    maximum = max(abs(averages[name] - target) for name, target in REFERENCE_V5.items())
    rows = payload["rows"]
    by_cell = {(float(row["noise"]), int(row["seed"]), row["representation"]): float(row["accuracy"])
               for row in rows}
    wins = sum(by_cell[(noise, seed, "Meta-FBOHN-v5-library")] > by_cell[(noise, seed, "FBOHN")]
               for noise in REFERENCE_TEST_A for seed in range(10))
    top_operator = next(iter(payload.get("operator_counts", {})), None)
    conclusion = (averages["Meta-FBOHN-v5-library"] > averages["Meta-FBOHN-v4-single"] > averages["FBOHN"]
                  and wins == 40 and top_operator == "mul")
    result = classification(conclusion, maximum, "Biblioteka v5 wygrywa z FBOHN w 40/40 komórek; mnożenie dominuje.")
    result.update({"aunc": averages, "wins_over_fbohn": wins, "top_operator": top_operator})
    return result


def classification(conclusion: bool, maximum: float | None, note: str) -> dict:
    if maximum is not None and conclusion and maximum <= .03:
        status = "CLOSE_NUMERIC_MATCH"
    elif conclusion:
        status = "CONCLUSION_MATCH"
    else:
        status = "NUMERIC_DIFFERENCE"
    return {"status": status, "scientific_conclusion_preserved": conclusion,
            "max_reported_numeric_delta": maximum,
            "max_reported_numeric_delta_pp": None if maximum is None else 100 * maximum,
            "note": note}


def compare(payload: dict, experiment_id: str) -> dict:
    program = PROGRAM_BY_ID[experiment_id]
    if program == "v1": return compare_v1(payload)
    if program == "testA": return compare_test_a(payload)
    if program == "v2": return compare_v2(payload, experiment_id)
    if program == "v3": return compare_v3(payload)
    if program == "v4": return compare_v4(payload)
    return compare_v5(payload)


def execute_program(program: str):
    checkpoint = ROOT / "reproduced" / "stage_15_checkpoint" / program
    checkpoint.mkdir(parents=True, exist_ok=True)
    summary = checkpoint / "summary.json"
    complete = checkpoint / "complete.json"
    if summary.exists() and complete.exists():
        try:
            payload = json.loads(summary.read_text(encoding="utf-8"))
            marker = json.loads(complete.read_text(encoding="utf-8"))
            if marker.get("status") == "PASS":
                return payload, 0.0, 0, True, ""
        except Exception:
            pass
    command = [sys.executable, "-u", str(ROOT / "tools" / "execute_historical_stage_15.py"),
               "--program", program, "--checkpoint", str(checkpoint)]
    start = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                               text=True, encoding="utf-8", errors="replace",
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    last = start
    last_progress = ""
    while process.poll() is None:
        now = time.perf_counter()
        if now - last >= 60:
            try:
                progress = json.loads((checkpoint / "progress.json").read_text(encoding="utf-8"))
                last_progress = f" | checkpoint {progress['completed']}/{progress['total']}"
            except Exception:
                pass
            print(f"{program}: nadal działa | {now-start:.0f} s{last_progress}", flush=True)
            last = now
        if now - start >= 259200:
            process.terminate()
            stdout, stderr = process.communicate()
            return {}, now - start, 124, False, stdout + "\n" + stderr
        time.sleep(1)
    stdout, stderr = process.communicate()
    duration = time.perf_counter() - start
    if process.returncode != 0 or not summary.exists():
        return {}, duration, process.returncode, False, stdout + "\n" + stderr
    return json.loads(summary.read_text(encoding="utf-8")), duration, 0, False, stdout + "\n" + stderr


def probe(experiment_id: str, raw: Path) -> dict:
    start = time.perf_counter()
    completed = subprocess.run([sys.executable, str(ROOT / "tools" / "smoke_stage_15.py"), "--only", experiment_id],
                               cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    (raw / f"{experiment_id}_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (raw / f"{experiment_id}_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    passed = completed.returncode == 0
    return {"execution_status": "PASS" if passed else "FAILED", "return_code": completed.returncode,
            "duration_seconds": round(time.perf_counter() - start, 6), "execution_mode": "SMOKE_PROBE",
            "historical_code_modified": False,
            "comparison": {"status": "SMOKE_PROBE_PASS" if passed else "SMOKE_PROBE_FAILED",
                           "scientific_conclusion_preserved": None}}


def manifest(output: Path) -> None:
    target = output / "MANIFEST_SHA256.txt"
    rows = [f"{digest(path.read_bytes())}  {path.relative_to(output).as_posix()}"
            for path in sorted(output.rglob("*")) if path.is_file() and path != target]
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--only", choices=IDS)
    args = parser.parse_args()
    selected = [args.only] if args.only else SMOKE if args.smoke else IDS
    mode = "only" if args.only else "smoke" if args.smoke else "full"
    stamp = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "reproduced" / "stage_15_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results, program_cache = {}, {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if args.smoke:
            row = probe(experiment_id, raw)
        else:
            program = PROGRAM_BY_ID[experiment_id]
            if program not in program_cache:
                program_cache[program] = execute_program(program)
            payload, duration, return_code, reused, log = program_cache[program]
            (raw / f"{experiment_id}_stdout.txt").write_text(log, encoding="utf-8")
            (raw / f"{experiment_id}_stderr.txt").write_text("", encoding="utf-8")
            (raw / f"{experiment_id}_result.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            passed = return_code == 0 and bool(payload)
            row = {"execution_status": "PASS" if passed else "FAILED", "return_code": return_code,
                   "duration_seconds": round(duration, 6),
                   "execution_mode": "HISTORICAL_FULL_SUITE_WITH_CELL_CHECKPOINTS",
                   "source_boundary": "FULL_SUITE", "historical_code_modified": False,
                   "checkpoint_reused": reused,
                   "comparison": compare(payload, experiment_id) if passed else {
                       "status": "EXECUTION_FAILED", "scientific_conclusion_preserved": False}}
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)

    report = {"stage": "15", "mode": mode, "created_utc": stamp, "source_chronology": selected,
              "historical_code_modified": False,
              "environment": {"python": sys.version, "platform": platform.platform()}, "experiments": results}
    (output / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Etap 15 — raport wykonania", "", "| # | ID | Wykonanie | Porównanie | Czas [s] |",
             "|---:|---|---|---|---:|"]
    for index, experiment_id in enumerate(selected, 1):
        row = results[experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += ["", "Wszystkie siedem jednostek korzysta z pełnego, niezmienionego listingu 71.",
              "Wrapper checkpointów dzieli protokół na komórki seed × noise i nie zmienia kodu historycznego."]
    (output / "REPRODUCTION_REPORT_PL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest(output)
    latest = ROOT / "reproduced" / "stage_15_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    print(f"RESULTS: {output.resolve()}")
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_15_RESULTS_{stamp}"), "zip", root_dir=output)
        print(f"ZIP: {Path(archive).resolve()}")
    return 0 if all(row["execution_status"] == "PASS" for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
