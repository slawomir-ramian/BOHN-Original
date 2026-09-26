#!/usr/bin/env python3
"""Uruchom Etap 08 w kolejności PDF-a, z checkpointem i heartbeat."""
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
BASE = ROOT / "experiments" / "06_learnable_sinkhorn"
SOURCE_CHRONOLOGY = [
    "LS-001", "LS-002", "LS-003", "LS-004", "LS-005", "LS-006",
    "LD-001", "LD-002", "LD-003", "LD-004", "LD-005",
]
SMOKE = ["LS-001", "LS-002", "LD-001", "LD-002", "LD-004", "LD-005"]
AUDITED_ONLY = {"LS-002", "LS-003", "LS-004", "LS-005", "LS-006"}
SHARED_OWNER = {"LD-002": "LD-001", "LD-003": "LD-001", "LD-005": "LD-004"}
PUBLISHED = {
    "LS-001": {"A_sbohn_inpdep": 0.878, "B_mlp": 0.719, "B_sbohn_inpdep": 0.722},
    "LD-001": {"naive_ds_0.001": 0.3447, "log_ds_0.001": 0.3001},
    "LD-002": {"fixed_acc": 0.893},
    "LD-003": {"no_reg_entropy": 1.637, "ent_0.1_entropy": 1.223},
    "LD-004": {"no_reg_acc": 0.876, "no_reg_entropy": 0.586},
    "LD-005": {"model_acc": 0.828},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def close_status(conclusion: bool, deltas: list[float], tolerance: float = 0.03) -> str:
    if conclusion and deltas and max(deltas) <= tolerance:
        return "CLOSE_NUMERIC_MATCH"
    if conclusion:
        return "CONCLUSION_MATCH"
    return "NUMERIC_DIFFERENCE"


def summary_value(text: str, label: str, task: str) -> float:
    pattern = rf"^{re.escape(label)}\s+{re.escape(task)}\s+([0-9]+(?:\.[0-9]+)?)\s+\d+\s+"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"Brak wiersza podsumowania: {label} / {task}")
    return float(match.group(1))


def comparison(experiment_id: str, stdout_text: str, result_data: dict) -> dict:
    try:
        if experiment_id == "LS-001":
            actual = {
                "A_sbohn_v1_fixed": summary_value(stdout_text, "SBOHN-v1 tau=1.0", "A(flip)"),
                "A_sbohn_v1_anneal": summary_value(stdout_text, "SBOHN-v1 tau-cos", "A(flip)"),
                "A_sbohn_inpdep": summary_value(stdout_text, "SBOHN-InpDep", "A(flip)"),
                "B_mlp": summary_value(stdout_text, "MLP-B", "B(blind)"),
                "B_sbohn_inpdep": summary_value(stdout_text, "SBOHN-InpDep-B", "B(blind)"),
            }
            conclusion = actual["A_sbohn_v1_anneal"] > actual["A_sbohn_v1_fixed"] and actual["B_sbohn_inpdep"] > actual["B_mlp"]
            deltas = [abs(actual[key] - value) for key, value in PUBLISHED[experiment_id].items()]
            note = "Kontrola annealingu Task A oraz przewagi InpDep nad MLP w Task B."
        elif experiment_id == "LD-001":
            row = result_data["test_a"]["0.001"]
            actual = {"naive_ds_0.001": row["naive_ds"], "log_ds_0.001": row["log_ds"], "naive_ok": row["naive_ok"], "log_ok": row["log_ok"]}
            conclusion = bool(row["naive_ok"] and row["log_ok"] and row["log_ds"] < row["naive_ds"])
            deltas = [abs(actual[key] - value) for key, value in PUBLISHED[experiment_id].items()]
            note = "Obie wersje są skończone; przy tau=0.001 log-domain ma mniejszy błąd DS."
        elif experiment_id == "LD-002":
            rows = result_data["test_b"]
            fixed = float(rows["fixed_0.5"]["final_acc"])
            actual = {"fixed_acc": fixed, "all_stable": all(not row["nan"] for row in rows.values()), "accuracies": {key: row["final_acc"] for key, row in rows.items()}}
            conclusion = actual["all_stable"] and fixed >= max(float(row["final_acc"]) for row in rows.values()) - 1e-9
            deltas = [abs(fixed - PUBLISHED[experiment_id]["fixed_acc"])]
            note = "Kontrola 5/5 stabilnych wariantów i najlepszego wyniku dla stałego tau=0.5."
        elif experiment_id == "LD-003":
            rows = result_data["test_c"]
            no_reg = rows["no_reg"]
            ent = rows["ent_0.1"]
            actual = {"no_reg_entropy": no_reg["entropy"], "ent_0.1_entropy": ent["entropy"], "no_reg_acc": no_reg["acc"], "ent_0.1_acc": ent["acc"]}
            conclusion = ent["entropy"] < no_reg["entropy"] and ent["acc"] >= no_reg["acc"] - 0.02
            deltas = [abs(actual[key] - value) for key, value in PUBLISHED[experiment_id].items()]
            note = "Kontrola spadku entropii bez materialnej utraty accuracy dla lambda_ent=0.1."
        elif experiment_id == "LD-004":
            rows = result_data["test_d"]
            no_reg = rows["no_reg_anneal"]
            actual = {"no_reg_acc": no_reg["acc"], "no_reg_entropy": no_reg["entropy"], "accuracies": {key: row["acc"] for key, row in rows.items()}}
            conclusion = no_reg["acc"] >= max(float(row["acc"]) for row in rows.values()) - 1e-9 and no_reg["entropy"] < 1.0
            deltas = [abs(actual[key] - value) for key, value in PUBLISHED[experiment_id].items()]
            note = "Kontrola naturalnie niskiej entropii i przewagi wariantu bez regularyzacji."
        elif experiment_id == "LD-005":
            rows = result_data["test_e"]
            matrices = rows["matrices"]
            actual = {"model_acc": rows["model_acc"], "valid_permutations": [row["is_valid_perm"] for row in matrices], "unique_columns": [row["n_unique"] for row in matrices], "closest_soft": [row["closest_soft"][0] for row in matrices]}
            conclusion = len(matrices) == 3 and not any(actual["valid_permutations"])
            deltas = [abs(actual["model_acc"] - PUBLISHED[experiment_id]["model_acc"])]
            note = "Kontrola braku twardych permutacji i złożonej struktury algebraicznej."
        else:
            raise ValueError(experiment_id)
        return {
            "status": close_status(conclusion, deltas),
            "scientific_conclusion_preserved": conclusion,
            "max_reported_numeric_delta": max(deltas) if deltas else None,
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
    return "sbohn_results.json" if experiment_id == "LS-001" else "sbohn_logdomain_results.json"


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
            "note": "Opublikowany wspólny listing nie zawiera kodu docelowego tej tabeli; zachowano dokładny wynik źródłowy.",
        },
    }


def run_process(experiment_id: str, raw: Path, runtime_tmp: Path, smoke: bool = False) -> dict:
    stdout_path = raw / f"{experiment_id}_stdout.txt"
    stderr_path = raw / f"{experiment_id}_stderr.txt"
    if smoke:
        smoke_path = ROOT / "tools" / "smoke_stage_08.py"
        args = [sys.executable, str(smoke_path), "--only", experiment_id]
        executed = str(smoke_path.relative_to(ROOT)).replace("\\", "/")
    else:
        source = source_path(experiment_id)
        wrapper = ROOT / "tools" / "execute_historical_stage_08.py"
        unit_tmp = runtime_tmp / experiment_id
        args = [sys.executable, "-u", str(wrapper), str(source), "--tmp-dir", str(unit_tmp)]
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
        compare = comparison(experiment_id, stdout_text, result_data)
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
        "comparison": comparison(experiment_id, stdout.read_text(encoding="utf-8", errors="replace"), result_data),
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
        "# Etap 08 — raport wykonania", "",
        "Jednostki wykonano w kolejności PDF-a. Wynik techniczny jest oddzielony od zgodności numerycznej.", "",
        "| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for index, experiment_id in enumerate(payload["source_chronology"], 1):
        row = payload["experiments"][experiment_id]
        lines.append(f"| {index} | {experiment_id} | {row['execution_mode']} | {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.3f} |")
    lines += [
        "", "## Granica źródłowa", "",
        "`LS-002`–`LS-006` mają tabele wynikowe, lecz przypisany wspólny listing 53 nie zawiera kodu tych pięciu eksperymentów. "
        "Dlatego zachowano je jako `AUDITED_REPORTED_RESULT`, bez tworzenia ukrytej rekonstrukcji.",
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
    output = args.output_dir or ROOT / "reproduced" / "stage_08_runs" / stamp
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
        checkpoint = {"stage": "08", "run_utc": now.isoformat(), "mode": mode, "source_chronology": selected, "completed_units": list(results), "experiments": results}
        (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    versions = {}
    for module, key in (("numpy", "numpy"), ("sklearn", "scikit_learn"), ("torch", "torch")):
        try:
            versions[key] = __import__(module).__version__
        except ImportError:
            versions[key] = None
    payload = {
        "stage": "08", "run_utc": now.isoformat(), "mode": mode,
        "source_chronology": selected, "full_source_chronology": SOURCE_CHRONOLOGY,
        "environment": {"python": sys.version, "platform": platform.platform(), **versions, "processor_count": os.cpu_count()},
        "source_boundary": {"shared_listing": 53, "target_code_absent_for": sorted(AUDITED_ONLY)},
        "experiments": results,
    }
    (output / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "REPRODUCTION_REPORT_PL.md").write_text(make_report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / "stage_08_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text((str(output.relative_to(ROOT)).replace("\\", "/") if output.is_relative_to(ROOT) else str(output)) + "\n", encoding="utf-8")
    make_manifest(output)
    archive = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        archive = Path(shutil.make_archive(str(artifacts / f"BOHN_ORIGINAL_STAGE_08_RESULTS_{stamp}"), "zip", root_dir=output))
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
