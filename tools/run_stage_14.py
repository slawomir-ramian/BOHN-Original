#!/usr/bin/env python3
"""Runner Etapu 14: sześć audytów i trzy pełne historyczne programy."""
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
IDS = ["MOE-001", "MOE-009", "MOE-002", "MOE-003", "MOE-004", "MOE-005", "MOE-006", "MOE-007", "MOE-008"]
SMOKE = ["MOE-001", "MOE-004", "MOE-006", "MOE-008"]
PROGRAM_BY_ID = {"MOE-004": "hard_assign", "MOE-006": "confidence", "MOE-008": "hybrid"}
PROGRAM_LEVELS = {"MOE-004": "FULL", "MOE-006": "FULL_SHARED_LISTING", "MOE-008": "FULL"}
AUDIT_LEVELS = {
    "MOE-001": "SOURCE_FRAGMENT_ONLY",
    "MOE-009": "SOURCE_FRAGMENT_ONLY",
    "MOE-002": "SOURCE_FRAGMENT_ONLY",
    "MOE-003": "SOURCE_FRAGMENT_ONLY",
    "MOE-005": "SHARED_LISTING_TARGET_CODE_ABSENT",
    "MOE-007": "SHARED_LISTING_TARGET_CODE_ABSENT",
}
DOMAINS = ["MNIST", "Fashion", "KMNIST"]
PUB_HARD_ACC = {"MNIST": 93.0, "Fashion": 87.4, "KMNIST": 87.2}
PUB_HARD_ROUTE = {"MNIST": [99.8, 0.0, 0.2, 0.0], "Fashion": [0.0, 99.8, 0.2, 0.0], "KMNIST": [0.2, 0.0, 99.8, 0.0]}
PUB_CONFIDENCE = {
    "max_logit": {"MNIST": 94.8, "Fashion": 62.2, "KMNIST": 71.5},
    "confidence": {"MNIST": 92.9, "Fashion": 58.6, "KMNIST": 68.3},
    "margin": {"MNIST": 91.6, "Fashion": 57.4, "KMNIST": 66.1},
}
PUB_HYBRID = {"MNIST": (96.8, 96.8, [100.0, 0.0, 0.0, 0.0]),
              "Fashion": (89.0, 89.0, [0.0, 99.8, 0.2, 0.0]),
              "KMNIST": (85.6, 85.6, [0.0, 0.0, 100.0, 0.0])}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_gate(text: str, n=4) -> list[float]:
    pairs = {int(i): float(v) for i, v in re.findall(r"E([0-9]+):([0-9.]+)%", text)}
    return [pairs.get(i, 0.0) for i in range(n)]


def parse_hard_assign(text: str) -> dict:
    result = {}
    for domain, acc, gate_text in re.findall(
            r"^  (MNIST|Fashion|KMNIST): ([0-9.]+)% \| Gate: \[(.*)\]$", text, re.M):
        result[domain] = {"accuracy": float(acc), "gate": parse_gate(gate_text)}
    return result


def parse_confidence(text: str) -> dict:
    result = {"oracle": {}, "methods": {name: {} for name in PUB_CONFIDENCE}}
    state = None
    for raw in text.splitlines():
        line = raw.strip()
        if line == "Oracle (hard assignment):":
            state = "oracle"
            continue
        match_method = re.fullmatch(r"(max_logit|confidence|margin) routing:", line)
        if match_method:
            state = match_method.group(1)
            continue
        match = re.match(r"(MNIST|Fashion|KMNIST): ([0-9.]+)%(?: \| Routing: \[(.*)\])?", line)
        if not match or state is None:
            continue
        domain, acc, gate_text = match.groups()
        if state == "oracle":
            result["oracle"][domain] = float(acc)
        else:
            result["methods"][state][domain] = {
                "accuracy": float(acc), "routing": parse_gate(gate_text or "", 3)}
    return result


def parse_hybrid(text: str) -> dict:
    result = {"domains": {}}
    for domain, gated, oracle, gate_text in re.findall(
            r"^  (MNIST|Fashion|KMNIST): Gated=([0-9.]+)%, Oracle=([0-9.]+)%, Gate=\[(.*)\]$", text, re.M):
        result["domains"][domain] = {
            "gated": float(gated), "oracle": float(oracle), "gate": parse_gate(gate_text)}
    for key, pattern in {
        "avg_gated": r"^  Avg Gated: ([0-9.]+)%$",
        "avg_oracle": r"^  Avg Oracle: ([0-9.]+)%$",
        "forgetting": r"^  Forgetting: ([0-9.]+)%$",
        "gate_overhead": r"^  Gate Overhead: ([0-9.]+)%$",
    }.items():
        match = re.search(pattern, text, re.M)
        if match:
            result[key] = float(match.group(1))
    return result


PARSERS = {"hard_assign": parse_hard_assign, "confidence": parse_confidence, "hybrid": parse_hybrid}


def complete(program: str, payload: dict) -> bool:
    if program == "hard_assign":
        return set(payload) == set(DOMAINS)
    if program == "confidence":
        return set(payload.get("oracle", {})) == set(DOMAINS) and all(set(payload.get("methods", {}).get(m, {})) == set(DOMAINS) for m in PUB_CONFIDENCE)
    return set(payload.get("domains", {})) == set(DOMAINS) and all(k in payload for k in ["avg_gated", "avg_oracle", "forgetting", "gate_overhead"])


def compare_hard(payload: dict) -> dict:
    deltas = []
    correct = True
    for index, domain in enumerate(DOMAINS):
        row = payload[domain]
        deltas.append(abs(row["accuracy"] - PUB_HARD_ACC[domain]))
        deltas.extend(abs(a - b) for a, b in zip(row["gate"], PUB_HARD_ROUTE[domain]))
        correct &= max(range(4), key=row["gate"].__getitem__) == index and row["gate"][index] >= 90 and row["accuracy"] >= 70
    return classify(correct, max(deltas), "Pełna specjalizacja domenowa i jakość gated.")


def compare_confidence(payload: dict) -> dict:
    deltas = []
    averages = {}
    for method, published in PUB_CONFIDENCE.items():
        actual = payload["methods"][method]
        deltas.extend(abs(actual[d]["accuracy"] - published[d]) for d in DOMAINS)
        averages[method] = sum(actual[d]["accuracy"] for d in DOMAINS) / 3
    conclusion = averages["max_logit"] >= averages["confidence"] >= averages["margin"]
    result = classify(conclusion, max(deltas), "Ranking max-logit > confidence > margin.")
    result["local_method_averages"] = averages
    return result


def compare_hybrid(payload: dict) -> dict:
    deltas = []
    correct = True
    for index, domain in enumerate(DOMAINS):
        row = payload["domains"][domain]
        pub_gated, pub_oracle, pub_gate = PUB_HYBRID[domain]
        deltas += [abs(row["gated"] - pub_gated), abs(row["oracle"] - pub_oracle)]
        deltas.extend(abs(a - b) for a, b in zip(row["gate"], pub_gate))
        correct &= max(range(4), key=row["gate"].__getitem__) == index and row["gate"][index] >= 90
    deltas += [abs(payload["avg_gated"] - 90.5), abs(payload["avg_oracle"] - 90.5),
               abs(payload["forgetting"] - 0.0), abs(payload["gate_overhead"] - 0.0)]
    correct &= payload["avg_gated"] >= 85 and payload["forgetting"] <= 5
    return classify(correct, max(deltas), "Hybrid BN/LN: poprawny routing, wysoka średnia i małe zapominanie.")


def classify(conclusion: bool, max_delta: float, note: str) -> dict:
    status = "CLOSE_NUMERIC_MATCH" if conclusion and max_delta <= 5 else "CONCLUSION_MATCH" if conclusion else "NUMERIC_DIFFERENCE"
    return {"status": status, "scientific_conclusion_preserved": conclusion,
            "max_reported_numeric_delta_pp": max_delta, "note": note}


COMPARATORS = {"hard_assign": compare_hard, "confidence": compare_confidence, "hybrid": compare_hybrid}


def execute_program(program: str):
    checkpoint = ROOT / "reproduced" / "stage_14_checkpoint" / program
    checkpoint.mkdir(parents=True, exist_ok=True)
    parsed = checkpoint / "parsed.json"
    stdout = checkpoint / "stdout.txt"
    stderr = checkpoint / "stderr.txt"
    marker = checkpoint / "complete.txt"
    try:
        cached = json.loads(parsed.read_text(encoding="utf-8"))
        if marker.exists() and complete(program, cached):
            return cached, 0.0, 0, stdout, stderr, True
    except Exception:
        pass
    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    command = [sys.executable, "-u", str(ROOT / "tools" / "execute_historical_stage_14.py"),
               "--program", program, "--marker", str(marker)]
    with stdout.open("w", encoding="utf-8", newline="\n") as out, stderr.open("w", encoding="utf-8", newline="\n") as err:
        process = subprocess.Popen(command, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", stdout=out, stderr=err)
        heartbeat = start
        while process.poll() is None:
            now = time.perf_counter()
            if now - heartbeat >= 60:
                print(f"{program}: nadal działa | {now-start:.0f} s", flush=True)
                heartbeat = now
            if now - start >= 43200:
                process.terminate()
                process.wait()
                return {}, now - start, 124, stdout, stderr, False
            time.sleep(1)
    duration = time.perf_counter() - start
    if process.returncode != 0:
        return {}, duration, process.returncode, stdout, stderr, False
    payload = PARSERS[program](stdout.read_text(encoding="utf-8", errors="replace"))
    if not complete(program, payload):
        return payload, duration, 65, stdout, stderr, False
    parsed.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload, duration, 0, stdout, stderr, False


def audit_row(experiment_id: str) -> dict:
    level = AUDIT_LEVELS[experiment_id]
    return {"execution_status": "PASS", "return_code": 0, "duration_seconds": 0.0,
            "execution_mode": "AUDIT_REPORTED_RESULT_SOURCE_BOUNDARY", "source_boundary": level,
            "historical_code_modified": False,
            "comparison": {"status": "AUDITED_REPORTED_RESULT", "scientific_conclusion_preserved": None,
                           "max_reported_numeric_delta_pp": None,
                           "note": "Brak opublikowanej pętli generującej tę tabelę."}}


def probe(experiment_id: str, raw: Path) -> dict:
    stdout = raw / f"{experiment_id}_stdout.txt"
    stderr = raw / f"{experiment_id}_stderr.txt"
    start = time.perf_counter()
    completed = subprocess.run([sys.executable, str(ROOT / "tools" / "smoke_stage_14.py"), "--only", experiment_id],
                               cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    stdout.write_text(completed.stdout, encoding="utf-8")
    stderr.write_text(completed.stderr, encoding="utf-8")
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
    output = ROOT / "reproduced" / "stage_14_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    program_cache = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if args.smoke:
            row = probe(experiment_id, raw)
        elif experiment_id in AUDIT_LEVELS:
            row = audit_row(experiment_id)
        else:
            program = PROGRAM_BY_ID[experiment_id]
            if program not in program_cache:
                program_cache[program] = execute_program(program)
            payload, duration, return_code, source_out, source_err, reused = program_cache[program]
            stdout = raw / f"{experiment_id}_stdout.txt"
            stderr = raw / f"{experiment_id}_stderr.txt"
            shutil.copyfile(source_out, stdout)
            shutil.copyfile(source_err, stderr)
            (raw / f"{experiment_id}_result.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            passed = return_code == 0 and complete(program, payload)
            row = {"execution_status": "PASS" if passed else "FAILED", "return_code": return_code,
                   "duration_seconds": round(duration, 6),
                   "execution_mode": "HISTORICAL_SHARED_SOURCE_WITH_COMPATIBILITY",
                   "source_boundary": PROGRAM_LEVELS[experiment_id], "historical_code_modified": False,
                   "runtime_compatibility": ["redirect_tmp_data"], "checkpoint_reused": reused,
                   "stdout_file": f"raw/{stdout.name}", "stderr_file": f"raw/{stderr.name}",
                   "comparison": COMPARATORS[program](payload) if passed else {
                       "status": "EXECUTION_FAILED", "scientific_conclusion_preserved": False}}
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)

    report = {"stage": "14", "mode": mode, "created_utc": stamp, "source_chronology": selected,
              "historical_code_modified": False,
              "environment": {"python": sys.version, "platform": platform.platform()}, "experiments": results}
    (output / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Etap 14 — raport wykonania", "", "| # | ID | Wykonanie | Porównanie | Czas [s] |",
             "|---:|---|---|---|---:|"]
    for index, experiment_id in enumerate(selected, 1):
        row = results[experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += ["", "Sześć jednostek pozostaje audytem z powodu braku opublikowanych pętli docelowych.",
              "Trzy pełne listingi historyczne zachowano bez zmian; `/tmp/data` przekierowano tylko w kopii wykonawczej."]
    (output / "REPRODUCTION_REPORT_PL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest(output)
    latest = ROOT / "reproduced" / "stage_14_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    print(f"RESULTS: {output.resolve()}")
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_14_RESULTS_{stamp}"), "zip", root_dir=output)
        print(f"ZIP: {Path(archive).resolve()}")
    return 0 if all(row["execution_status"] == "PASS" for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
