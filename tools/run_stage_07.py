#!/usr/bin/env python3
"""Uruchom Etap 07 w kolejności PDF-a z checkpointem i heartbeat."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "05_permutation_and_representation"
SOURCE_CHRONOLOGY = ["PL-001", "PL-002", "PL-003", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001", "HD-002", "HD-003", "CMP-001", "CMP-002"]
SMOKE = ["PL-001", "AR-001", "AR-004", "HD-001", "CMP-002"]
NARRATIVE_ONLY = {"PL-002", "PL-003", "HD-003", "CMP-001", "CMP-002"}
EXPECTED = {
    "PL-001": 0.9481,
    "AR-001": 0.9537,
    "AR-002": 0.9481,
    "AR-003": 0.9537,
    "AR-004": 0.7965,
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(text: str, label: str) -> float:
    match = re.search(rf"^{re.escape(label)}\s*([+-]?[0-9]+(?:\.[0-9]+)?)", text, re.MULTILINE)
    if not match:
        raise ValueError(f"Brak pola: {label}")
    return float(match.group(1))


def comparison(experiment_id: str, text: str) -> dict:
    try:
        if experiment_id == "PL-001":
            baseline = number(text, "Baseline x accuracy:")
            random_mean = number(text, "Random mean accuracy:")
            best = number(text, "Best evolved accuracy:")
            ok = best > baseline and best > random_mean
            actual = {"baseline": baseline, "random_mean": random_mean, "best": best}
            observed = best
        elif experiment_id == "AR-001":
            baseline = number(text, "Baseline x accuracy:")
            random_best = number(text, "Random best accuracy:")
            best = number(text, "Best evolved accuracy:")
            ok = best > baseline and best > random_best
            actual = {"baseline": baseline, "random_best": random_best, "best": best}
            observed = best
        elif experiment_id == "AR-002":
            baseline = number(text, "Baseline x accuracy:")
            random99 = number(text, "Random 99 accuracy:")
            best = number(text, "AR-v2 L1 accuracy:")
            ok = best > baseline and best > random99 and "Generated in Top10:" in text
            actual = {"baseline": baseline, "random99": random99, "best": best}
            observed = best
        elif experiment_id == "AR-003":
            baseline = number(text, "Baseline x accuracy:")
            best = number(text, "Best evolved accuracy:")
            ok = best > baseline and "best_vs_flip" in text and "best_vs_rot180" in text
            actual = {"baseline": baseline, "best": best}
            observed = best
        elif experiment_id == "AR-004":
            perm = number(text, "Mean pairwise perm similarity:")
            cka = number(text, "Mean pairwise CKA:")
            ok = perm < 0.10 and cka > 0.60
            actual = {"mean_pairwise_permutation_similarity": perm, "mean_pairwise_cka": cka}
            observed = cka
        elif experiment_id in {"HD-001", "HD-002"}:
            dimensions = [tuple(map(float, row)) for row in re.findall(r"d=\s*\d+\s+base=([0-9.]+)\s+sbohn=([0-9.]+)\s+gain=([0-9.]+)\s+wins=(\d+)/10", text)]
            samples = [tuple(map(float, row)) for row in re.findall(r"n=\s*\d+\s+base=([0-9.]+)\s+sbohn=([0-9.]+)\s+gain=([0-9.]+)\s+wins=(\d+)/10", text)]
            rows = dimensions if experiment_id == "HD-001" else samples
            expected_count = 4 if experiment_id == "HD-001" else 3
            ok = len(rows) == expected_count and all(sb > raw and int(wins) == 10 for raw, sb, gain, wins in rows)
            if experiment_id == "HD-002" and len(rows) == 3:
                ok = ok and rows[0][2] < rows[1][2] < rows[2][2]
            return {"status": "CONCLUSION_MATCH" if ok else "SCIENTIFIC_MISMATCH", "scientific_conclusion_preserved": ok, "max_reported_numeric_delta": None, "actual_summary": {"rows": rows}, "note": "SBOHN przewyższa baseline; kontrola wins i trendu."}
        else:
            raise ValueError(experiment_id)
        delta = abs(observed - EXPECTED[experiment_id])
        status = "CLOSE_NUMERIC_MATCH" if ok and delta <= 0.01 else ("CONCLUSION_MATCH" if ok else "SCIENTIFIC_MISMATCH")
        return {"status": status, "scientific_conclusion_preserved": ok, "max_reported_numeric_delta": delta, "actual_summary": actual, "note": "Kontrola wniosku merytorycznego i wartości referencyjnej."}
    except (ValueError, IndexError) as exc:
        return {"status": "UNPARSEABLE_OUTPUT", "scientific_conclusion_preserved": False, "max_reported_numeric_delta": None, "actual_summary": {}, "note": str(exc)}


def command(experiment_id: str, smoke: bool) -> tuple[list[str], str]:
    if smoke:
        path = ROOT / "tools" / "smoke_stage_07.py"
        return [sys.executable, str(path), "--only", experiment_id], str(path.relative_to(ROOT)).replace("\\", "/")
    historical = BASE / experiment_id / "historical"
    if experiment_id.startswith("HD-"):
        fragment1 = historical / "source_fragment_1_from_monograph.py"
        fragment2 = historical / "source_fragment_2_from_monograph.py"
        code = "from pathlib import Path; import sys; exec(Path(sys.argv[1]).read_text(encoding='utf-8') + '\\n' + Path(sys.argv[2]).read_text(encoding='utf-8'), {'__name__':'__main__'})"
        return [sys.executable, "-u", "-c", code, str(fragment1), str(fragment2)], "historical/listings_51_52_composed_in_memory"
    path = historical / "source_from_monograph.py"
    return [sys.executable, "-u", str(path)], str(path.relative_to(ROOT)).replace("\\", "/")


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
    return {"execution_status": "PASS", "return_code": 0, "duration_seconds": 0.0, "execution_mode": "AUDITED_REPORTED_RESULT", "executed_file": str(source.relative_to(ROOT)).replace("\\", "/"), "stdout_sha256": digest(stdout.read_bytes()), "stderr_sha256": digest(b""), "stderr_nonempty": False, "stdout_file": f"raw/{experiment_id}_stdout.txt", "stderr_file": f"raw/{experiment_id}_stderr.txt", "comparison": {"status": "AUDITED_REPORTED_RESULT", "scientific_conclusion_preserved": None, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Pełny kod nie został opublikowany; zachowano dokładny wynik źródłowy."}}


def run_process(experiment_id: str, raw: Path, smoke: bool = False) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    args, executed = command(experiment_id, smoke)
    start = time.perf_counter()
    timed_out = False
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(args, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", stdout=stdout, stderr=stderr)
        heartbeat = start
        while process.poll() is None:
            now = time.perf_counter()
            if now - heartbeat >= 60:
                print(f"{experiment_id}: nadal działa | {now - start:.0f} s", flush=True)
                heartbeat = now
            if now - start >= 28800:
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
            stderr.write("\n[RUNNER_TIMEOUT] Przekroczono 28800 s.\n")
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    if timed_out:
        compare = {"status": "TIMEOUT", "scientific_conclusion_preserved": False, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Techniczny limit czasu."}
    elif smoke:
        compare = {"status": "SMOKE_PROBE_PASS" if return_code == 0 else "SMOKE_PROBE_FAILED", "scientific_conclusion_preserved": None, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Smoke nie zastępuje pełnego programu."}
    else:
        compare = comparison(experiment_id, stdout_text)
    status = "TIMEOUT" if timed_out else ("PASS" if return_code == 0 else "FAILED")
    return {"execution_status": status, "return_code": return_code, "duration_seconds": round(time.perf_counter() - start, 6), "execution_mode": "SMOKE_PROBE" if smoke else "HISTORICAL_SOURCE", "executed_file": executed, "stdout_sha256": digest(stdout_text.encode()), "stderr_sha256": digest(stderr_text.encode()), "stderr_nonempty": bool(stderr_text.strip()), "stdout_file": f"raw/{experiment_id}_stdout.txt", "stderr_file": f"raw/{experiment_id}_stderr.txt", "comparison": compare}


def reuse_hd2(raw: Path, hd1: dict) -> dict:
    for suffix in ("stdout.txt", "stderr.txt"):
        shutil.copyfile(raw / f"HD-001_{suffix}", raw / f"HD-002_{suffix}")
    text = (raw / "HD-002_stdout.txt").read_text(encoding="utf-8", errors="replace")
    result = dict(hd1)
    result.update({"duration_seconds": 0.0, "execution_mode": "HISTORICAL_SOURCE_SHARED_RUN", "stdout_file": "raw/HD-002_stdout.txt", "stderr_file": "raw/HD-002_stderr.txt", "comparison": comparison("HD-002", text)})
    return result


def make_manifest(output: Path) -> None:
    manifest = output / "MANIFEST_SHA256.txt"
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != manifest:
            rows.append(f"{digest(path.read_bytes())}  {path.relative_to(output).as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_report(payload: dict) -> str:
    lines = ["# Etap 07 — raport wykonania", "", "Jednostki wykonano w kolejności PDF-a.", "", "| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |", "|---:|---|---|---|---|---:|"]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_mode']} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += ["", "`AUDITED_REPORTED_RESULT` oznacza brak pełnego kodu w publikacji, nie błąd. `HD-001` i `HD-002` są dwoma odczytami jednego opublikowanego programu."]
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
    output = args.output_dir or ROOT / "reproduced" / "stage_07_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if not smoke and experiment_id in NARRATIVE_ONLY:
            row = audited_result(experiment_id, raw)
        elif not smoke and experiment_id == "HD-002" and "HD-001" in results:
            row = reuse_hd2(raw, results["HD-001"])
        else:
            row = run_process(experiment_id, raw, smoke)
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)
        checkpoint = {"stage": "07", "run_utc": now.isoformat(), "mode": mode, "source_chronology": selected, "completed_units": list(results), "experiments": results}
        (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    versions = {}
    for module, key in (("numpy", "numpy"), ("pandas", "pandas"), ("sklearn", "scikit_learn")):
        try:
            versions[key] = __import__(module).__version__
        except ImportError:
            versions[key] = None
    payload = {"stage": "07", "run_utc": now.isoformat(), "mode": mode, "source_chronology": selected, "full_source_chronology": SOURCE_CHRONOLOGY, "environment": {"python": sys.version, "platform": platform.platform(), **versions, "processor_count": os.cpu_count()}, "experiments": results}
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(make_report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / "stage_07_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text((str(output.relative_to(ROOT)).replace("\\", "/") if output.is_relative_to(ROOT) else str(output)) + "\n", encoding="utf-8")
    make_manifest(output)
    archive = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = Path(shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_07_RESULTS_{stamp}"), "zip", root_dir=output))
    print(f"RESULTS: {output}")
    if archive:
        print(f"ZIP: {archive}")
    failed = any(row["execution_status"] != "PASS" or row["comparison"]["status"] in {"SCIENTIFIC_MISMATCH", "UNPARSEABLE_OUTPUT", "TIMEOUT"} for row in results.values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
