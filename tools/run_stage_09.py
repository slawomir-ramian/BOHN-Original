#!/usr/bin/env python3
"""Uruchom Etap 09 w kolejności PDF-a, z checkpointem i heartbeat."""
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
BASE = ROOT / "experiments" / "07_fractal_patch"
SOURCE_CHRONOLOGY = [
    "FR-001", "FR-004", "FR-002", "FR-003",
    "PT-001", "PT-002", "PT-003", "PT-004", "PT-005",
    "HR-001", "HR-002", "HR-003", "HR-004", "HR-005", "HR-006", "HR-007",
]
SMOKE = ["FR-001", "FR-002", "FR-003", "PT-001", "PT-003", "PT-004", "HR-003"]
AUDITED_ONLY = {
    "FR-001", "FR-004", "PT-003",
    "HR-001", "HR-002", "HR-003", "HR-004", "HR-005", "HR-006", "HR-007",
}
SHARED_OWNER = {
    "FR-003": "FR-002",
    "PT-002": "PT-001", "PT-004": "PT-001", "PT-005": "PT-001",
}
PUBLISHED = {
    "FR-002": {"m_MLP128": 0.9075, "m_F4L_h64": 0.9000},
    "FR-003": {"f_MLP96": 0.7975, "f_MLP128": 0.8125, "f_F4L": 0.8025},
    "PT-001": {"mlp": 0.916, "inpdep_4h_tau01": 0.918},
    "PT-002": {"mlp": 0.842, "inpdep_4h_tau01": 0.848},
    "PT-004": {"m_global_tau03": 0.864, "m_inpdep_1h_tau03": 0.916, "f_global_tau03": 0.740, "f_inpdep_1h_tau03": 0.832},
    "PT-005": {"m_1h_tau01": 0.908, "m_4h_tau01": 0.918, "f_1h_tau01": 0.822, "f_4h_tau01": 0.848},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def close_status(conclusion: bool, deltas: list[float], tolerance: float = 0.05) -> str:
    if conclusion and deltas and max(deltas) <= tolerance:
        return "CLOSE_NUMERIC_MATCH"
    if conclusion:
        return "CONCLUSION_MATCH"
    return "NUMERIC_DIFFERENCE"


def pt_accuracy(data: dict, dataset: str, index: int) -> float:
    return float(data[dataset][index]["acc"])


def comparison(experiment_id: str, result_data: dict) -> dict:
    try:
        if experiment_id == "FR-002":
            actual = {key: float(result_data[key]["acc"]) for key in ("m_F2L", "m_F3L", "m_F4L", "m_F4L_h64", "m_MLP128")}
            conclusion = actual["m_F4L_h64"] > actual["m_F2L"] and actual["m_F4L_h64"] >= actual["m_MLP128"] - 0.03
            note = "Kontrola transferu na MNIST, korzyści głębokości i małej luki względem MLP-128."
        elif experiment_id == "FR-003":
            actual = {key: float(result_data[key]["acc"]) for key in ("f_F2L", "f_F3L", "f_F4L", "f_MLP96", "f_MLP128")}
            conclusion = actual["f_F4L"] > actual["f_F2L"] and actual["f_F4L"] > actual["f_MLP96"]
            note = "Kontrola transferu na Fashion-MNIST i przewagi Frac-4L nad MLP-96."
        elif experiment_id in {"PT-001", "PT-002"}:
            dataset = "mnist" if experiment_id == "PT-001" else "fmnist"
            actual = {"mlp": pt_accuracy(result_data, dataset, 0), "inpdep_4h_tau01": pt_accuracy(result_data, dataset, 7)}
            conclusion = actual["inpdep_4h_tau01"] > actual["mlp"]
            note = "Kontrola opublikowanej przewagi Patch SBOHN InpDep 4H tau=0.1 nad MLP."
        elif experiment_id == "PT-004":
            actual = {
                "m_global_tau03": pt_accuracy(result_data, "mnist", 3),
                "m_inpdep_1h_tau03": pt_accuracy(result_data, "mnist", 4),
                "f_global_tau03": pt_accuracy(result_data, "fmnist", 3),
                "f_inpdep_1h_tau03": pt_accuracy(result_data, "fmnist", 4),
            }
            conclusion = actual["m_inpdep_1h_tau03"] > actual["m_global_tau03"] and actual["f_inpdep_1h_tau03"] > actual["f_global_tau03"]
            note = "Kontrola korzyści input-dependency na obu zbiorach."
        elif experiment_id == "PT-005":
            actual = {
                "m_1h_tau01": pt_accuracy(result_data, "mnist", 5),
                "m_4h_tau01": pt_accuracy(result_data, "mnist", 7),
                "f_1h_tau01": pt_accuracy(result_data, "fmnist", 5),
                "f_4h_tau01": pt_accuracy(result_data, "fmnist", 7),
            }
            conclusion = actual["m_4h_tau01"] > actual["m_1h_tau01"] and actual["f_4h_tau01"] > actual["f_1h_tau01"]
            note = "Kontrola korzyści czterech głów względem jednej głowy."
        else:
            raise ValueError(experiment_id)
        deltas = [abs(actual[key] - value) for key, value in PUBLISHED[experiment_id].items()]
        return {
            "status": close_status(conclusion, deltas),
            "scientific_conclusion_preserved": conclusion,
            "max_reported_numeric_delta": max(deltas),
            "actual_summary": actual,
            "note": note,
        }
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return {
            "status": "UNPARSEABLE_OUTPUT",
            "scientific_conclusion_preserved": False,
            "max_reported_numeric_delta": None,
            "actual_summary": {},
            "note": str(exc),
        }


def source_path(experiment_id: str) -> Path:
    return BASE / experiment_id / "historical" / "source_from_monograph.py"


def json_name(experiment_id: str) -> str:
    return "real_results.json" if experiment_id.startswith("FR-") else "patch_results.json"


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
    return {
        "execution_status": "PASS", "return_code": 0, "duration_seconds": 0.0,
        "execution_mode": "AUDITED_REPORTED_RESULT",
        "executed_file": str(source.relative_to(ROOT)).replace("\\", "/"),
        "stdout_sha256": digest(stdout.read_bytes()), "stderr_sha256": digest(b""),
        "stderr_nonempty": False, "stdout_file": f"raw/{experiment_id}_stdout.txt",
        "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "comparison": {
            "status": "AUDITED_REPORTED_RESULT", "scientific_conclusion_preserved": None,
            "max_reported_numeric_delta": None, "actual_summary": {},
            "note": "Zachowano dokładny wynik źródłowy bez konstruowania brakującego kodu historycznego.",
        },
    }


def run_process(experiment_id: str, raw: Path, runtime_tmp: Path, smoke: bool = False) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    if smoke:
        smoke_path = ROOT / "tools" / "smoke_stage_09.py"
        args = [sys.executable, str(smoke_path), "--only", experiment_id]
        executed = str(smoke_path.relative_to(ROOT)).replace("\\", "/")
    else:
        source = source_path(experiment_id)
        wrapper = ROOT / "tools" / "execute_historical_stage_09.py"
        unit_tmp = runtime_tmp / experiment_id
        cache = ROOT / "reproduced" / "stage_09_dataset_cache"
        args = [sys.executable, "-u", str(wrapper), str(source), "--run-dir", str(unit_tmp), "--cache-dir", str(cache)]
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
    result_data = {}
    historical_json_file = None
    if not smoke and not timed_out and return_code == 0:
        generated = runtime_tmp / experiment_id / json_name(experiment_id)
        if generated.exists():
            historical_json_file = raw / f"{experiment_id}_historical_result.json"
            shutil.copyfile(generated, historical_json_file)
            result_data = json.loads(historical_json_file.read_text(encoding="utf-8"))
    if timed_out:
        compare = {"status": "TIMEOUT", "scientific_conclusion_preserved": False, "max_reported_numeric_delta": None, "actual_summary": {}, "note": "Techniczny limit czasu."}
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
        "execution_mode": "SMOKE_PROBE" if smoke else "HISTORICAL_SOURCE",
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
    stdout = raw / f"{experiment_id}_stdout.txt"
    result_json = raw / f"{experiment_id}_historical_result.json"
    result_data = json.loads(result_json.read_text(encoding="utf-8"))
    row = dict(owner_row)
    row.update({
        "duration_seconds": 0.0,
        "execution_mode": "HISTORICAL_SOURCE_SHARED_RUN",
        "stdout_file": f"raw/{experiment_id}_stdout.txt",
        "stderr_file": f"raw/{experiment_id}_stderr.txt",
        "historical_result_file": f"raw/{experiment_id}_historical_result.json",
        "stdout_sha256": digest(stdout.read_bytes()),
        "historical_result_sha256": digest(result_json.read_bytes()),
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
        "# Etap 09 — raport wykonania", "",
        "Jednostki wykonano w kolejności PDF-a. Status techniczny jest oddzielony od zgodności naukowej.", "",
        "| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_mode']} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += [
        "", "## Granica źródłowa", "",
        "Sześć jednostek ma kompletny kod wykonywalny, zorganizowany w dwóch wspólnych programach. "
        "Dziesięć jednostek ma opublikowane wyniki bez kompletnego kodu docelowego i pozostaje `AUDITED_REPORTED_RESULT`.",
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
    output = args.output_dir or ROOT / "reproduced" / "stage_09_runs" / stamp
    raw = output / "raw"
    runtime_tmp = output / "runtime_tmp"
    raw.mkdir(parents=True, exist_ok=True)
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if not smoke and experiment_id in AUDITED_ONLY:
            row = audited_result(experiment_id, raw)
        elif not smoke and experiment_id in SHARED_OWNER and SHARED_OWNER[experiment_id] in results:
            row = reuse_shared(experiment_id, SHARED_OWNER[experiment_id], raw, results[SHARED_OWNER[experiment_id]])
        else:
            row = run_process(experiment_id, raw, runtime_tmp, smoke)
        results[experiment_id] = row
        print(f"{experiment_id}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s", flush=True)
        checkpoint = {"stage": "09", "run_utc": now.isoformat(), "mode": mode, "source_chronology": selected, "completed_units": list(results), "experiments": results}
        (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    versions = {}
    for module, key in (("numpy", "numpy"), ("sklearn", "scikit_learn"), ("torch", "torch")):
        try:
            versions[key] = __import__(module).__version__
        except ImportError:
            versions[key] = None
    payload = {
        "stage": "09", "run_utc": now.isoformat(), "mode": mode,
        "source_chronology": selected, "full_source_chronology": SOURCE_CHRONOLOGY,
        "environment": {"python": sys.version, "platform": platform.platform(), **versions, "processor_count": os.cpu_count()},
        "source_boundary": {"executable_units": 6, "shared_programs": 2, "audited_only": sorted(AUDITED_ONLY)},
        "experiments": results,
    }
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(make_report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / "stage_09_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text((str(output.relative_to(ROOT)).replace("\\", "/") if output.is_relative_to(ROOT) else str(output)) + "\n", encoding="utf-8")
    make_manifest(output)
    archive = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = Path(shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_09_RESULTS_{stamp}"), "zip", root_dir=output))
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
