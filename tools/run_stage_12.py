#!/usr/bin/env python3
"""Uruchom Etap 12 w kolejności PDF-a i sklasyfikuj wyniki jawnie."""
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
IDS = ["SOTA-001", "SOTA-002"]
PUBLISHED_ACCURACY = {
    "MLP": 78.0, "ViT-Tiny": 66.6, "Fractal_SBOHN_v2": 54.2, "CNN": 35.2,
}
PUBLISHED_PARAMS_28 = {
    "MLP": 235146, "ViT-Tiny": 71946, "Fractal_SBOHN_v2": 54298, "CNN": 23946,
}
PUBLISHED_TIMES = {
    "Fractal_SBOHN_v2": {"28": 1.08, "56": 1.03, "112": 1.10, "224": 1.18, "448": 1.50},
    "CNN": {"28": 0.25, "56": 0.60, "112": 1.05, "224": 8.67, "448": 10.17},
    "ViT-Tiny": {"28": 1.06, "56": 1.06, "112": 1.05, "224": 1.11, "448": 1.32},
}
PUBLISHED_SCALING = {"Fractal_SBOHN_v2": 0.059, "CNN": 0.668, "ViT-Tiny": 0.040}
PUBLISHED_PARAMS = {
    "Fractal_SBOHN_v2": {"28": 54298, "56": 63706, "112": 101338, "224": 251866, "448": 853978},
    "CNN": {"28": 23946, "56": 23946, "112": 23946, "224": 23946, "448": 23946},
    "ViT-Tiny": {"28": 71946, "56": 81354, "112": 118986, "224": 269514, "448": 871626},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def comparison(experiment_id: str, payload: dict) -> dict:
    try:
        if experiment_id == "SOTA-001":
            params_exact = all(int(payload[name]["params"]) == expected for name, expected in PUBLISHED_PARAMS_28.items())
            deltas = {name: abs(float(payload[name]["acc"]) - expected) for name, expected in PUBLISHED_ACCURACY.items()}
            order = sorted(PUBLISHED_ACCURACY, key=lambda name: float(payload[name]["acc"]), reverse=True)
            conclusion = order == ["MLP", "ViT-Tiny", "Fractal_SBOHN_v2", "CNN"]
            close = params_exact and conclusion and max(deltas.values()) <= 5.0
            status = "CLOSE_NUMERIC_MATCH" if close else "CONCLUSION_MATCH" if params_exact and conclusion else "NUMERIC_DIFFERENCE"
            return {
                "status": status,
                "architecture_contract_status": "EXACT_MATCH" if params_exact else "DIFFERENT",
                "scientific_conclusion_preserved": conclusion,
                "max_accuracy_delta_pp": max(deltas.values()),
                "accuracy_deltas_pp": deltas,
                "hardware_dependent": ["train_s"],
                "note": "Brak ziarna w historycznym listingu oznacza stochastyczną dokładność; czas treningu zależy od sprzętu.",
            }
        params_exact = all(
            int(payload[name]["params"][resolution]) == expected
            for name, values in PUBLISHED_PARAMS.items() for resolution, expected in values.items()
        )
        timing_deltas = [
            abs(float(payload[name]["times"][resolution]) - expected)
            for name, values in PUBLISHED_TIMES.items() for resolution, expected in values.items()
        ]
        exponent_deltas = {
            name: abs(float(payload[name]["scaling_exp"]) - expected)
            for name, expected in PUBLISHED_SCALING.items()
        }
        sbohn_exp = float(payload["Fractal_SBOHN_v2"]["scaling_exp"])
        cnn_exp = float(payload["CNN"]["scaling_exp"])
        vit_exp = float(payload["ViT-Tiny"]["scaling_exp"])
        conclusion = sbohn_exp < cnn_exp and vit_exp < cnn_exp
        close = params_exact and conclusion and max(timing_deltas) <= 2.0 and max(exponent_deltas.values()) <= 0.15
        status = "CLOSE_NUMERIC_MATCH" if close else "CONCLUSION_MATCH" if params_exact and conclusion else "NUMERIC_DIFFERENCE"
        return {
            "status": status,
            "architecture_contract_status": "EXACT_MATCH" if params_exact else "DIFFERENT",
            "scientific_conclusion_preserved": conclusion,
            "max_timing_delta_ms": max(timing_deltas),
            "max_scaling_exponent_delta": max(exponent_deltas.values()),
            "hardware_dependent": ["times", "scaling_exp", "est_4k_ms"],
            "note": "Pomiary time.time z trzema powtórzeniami są sprzętowo zależne; kontrakt parametrów oceniono osobno.",
        }
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "status": "UNPARSEABLE_OUTPUT", "architecture_contract_status": "UNKNOWN",
            "scientific_conclusion_preserved": False, "note": str(exc),
        }


def valid_checkpoint(path: Path, experiment_id: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = set(PUBLISHED_ACCURACY) if experiment_id == "SOTA-001" else set(PUBLISHED_PARAMS)
        return required.issubset(payload)
    except (OSError, ValueError, TypeError):
        return False


def execute(experiment_id: str, raw: Path) -> dict:
    checkpoint_root = ROOT / "reproduced" / "stage_12_checkpoint"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    checkpoint = checkpoint_root / f"{experiment_id}.json"
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    reused = valid_checkpoint(checkpoint, experiment_id)
    started = time.perf_counter()
    return_code = 0
    if reused:
        stdout_path.write_text("CHECKPOINT REUSED\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
    else:
        args = [
            sys.executable, "-u", str(ROOT / "tools" / "execute_historical_stage_12.py"),
            "--id", experiment_id, "--output", str(checkpoint),
        ]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
            process = subprocess.Popen(args, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", stdout=stdout, stderr=stderr)
            heartbeat = started
            while process.poll() is None:
                now = time.perf_counter()
                if now - heartbeat >= 60:
                    print(f"{experiment_id}: nadal dziala | {now - started:.0f} s", flush=True)
                    heartbeat = now
                if now - started >= 21600:
                    process.terminate()
                    try:
                        process.wait(30)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
                    return_code = 124
                    break
                time.sleep(1)
            if return_code == 0:
                return_code = process.returncode
    duration = time.perf_counter() - started
    passed = return_code == 0 and valid_checkpoint(checkpoint, experiment_id)
    payload = json.loads(checkpoint.read_text(encoding="utf-8")) if passed else {}
    result_copy = raw / f"{experiment_id}_historical_result.json"
    if passed:
        shutil.copyfile(checkpoint, result_copy)
    compare = comparison(experiment_id, payload) if passed else {
        "status": "EXECUTION_FAILED", "architecture_contract_status": "UNKNOWN",
        "scientific_conclusion_preserved": False, "note": "Program historyczny zakonczyl sie bledem.",
    }
    row = {
        "execution_status": "PASS" if passed else "FAILED",
        "return_code": return_code,
        "duration_seconds": round(duration, 6),
        "execution_mode": "HISTORICAL_SOURCE_WITH_PATH_COMPATIBILITY",
        "source_code_level": "FULL_SOURCE",
        "historical_code_modified": False,
        "checkpoint_reused": reused,
        "stdout_file": f"raw/{stdout_path.name}",
        "stderr_file": f"raw/{stderr_path.name}",
        "stdout_sha256": digest(stdout_path.read_bytes()),
        "stderr_sha256": digest(stderr_path.read_bytes()),
        "comparison": compare,
    }
    if passed:
        row["historical_result_file"] = f"raw/{result_copy.name}"
        row["historical_result_sha256"] = digest(result_copy.read_bytes())
    return row


def probe(experiment_id: str, raw: Path) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "smoke_stage_12.py"), "--only", experiment_id],
        cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
    passed = completed.returncode == 0
    return {
        "execution_status": "PASS" if passed else "FAILED", "return_code": completed.returncode,
        "duration_seconds": round(time.perf_counter() - started, 6), "execution_mode": "SMOKE_PROBE",
        "source_code_level": "FULL_SOURCE", "historical_code_modified": False,
        "stdout_file": f"raw/{stdout_path.name}", "stderr_file": f"raw/{stderr_path.name}",
        "stdout_sha256": digest(stdout_path.read_bytes()), "stderr_sha256": digest(stderr_path.read_bytes()),
        "comparison": {"status": "SMOKE_PROBE_PASS" if passed else "SMOKE_PROBE_FAILED", "scientific_conclusion_preserved": None},
    }


def make_manifest(output: Path) -> None:
    manifest = output / "MANIFEST_SHA256.txt"
    rows = [f"{digest(path.read_bytes())}  {path.relative_to(output).as_posix()}" for path in sorted(output.rglob("*")) if path.is_file() and path != manifest]
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")


def report(payload: dict) -> str:
    lines = [
        "# Etap 12 — raport wykonania", "",
        "Pozycje 88–89 wykonano w kolejności PDF-a. Historyczne listingi pozostały niezmienione.", "",
        "| # | ID | Wykonanie | Porównanie | Kontrakt architektury | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        contract = row["comparison"].get("architecture_contract_status", "—")
        lines.append(f"| {index} | {experiment_id} | {row['execution_status']} | {row['comparison']['status']} | {contract} | {row['duration_seconds']:.3f} |")
    lines += [
        "", "## Interpretacja", "",
        "Czasy treningu i inferencji są zależne od CPU, wersji bibliotek i obciążenia systemu. "
        "Dlatego zgodność liczby parametrów oraz wniosku o skalowaniu jest raportowana niezależnie od dokładności czasów.",
        "", "`NUMERIC_DIFFERENCE` nie oznacza awarii programu; opisuje różnicę względem historycznej tabeli.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--only", choices=IDS)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    selected = [args.only] if args.only else IDS
    mode = "only" if args.only else "smoke" if args.smoke else "full"
    stamp = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or ROOT / "reproduced" / "stage_12_runs" / stamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        row = probe(experiment_id, raw) if args.smoke else execute(experiment_id, raw)
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)
    payload = {
        "stage": "12", "mode": mode, "created_utc": stamp,
        "source_chronology": selected, "historical_code_modified": False,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "experiments": results,
    }
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(report(payload), encoding="utf-8")
    make_manifest(output)
    latest = ROOT / "reproduced" / "stage_12_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    print(f"RESULTS: {output.resolve()}")
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = artifacts / f"BOHN_ORIGINAL_STAGE_12_RESULTS_{stamp}"
        zip_path = shutil.make_archive(str(archive), "zip", root_dir=output)
        print(f"ZIP: {Path(zip_path).resolve()}")
    return 0 if all(row["execution_status"] == "PASS" for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
