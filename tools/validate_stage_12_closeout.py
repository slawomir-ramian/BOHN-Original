#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 12 z rozdzieleniem kontraktu i czasu."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_12_runs" / "20260927T184235Z"
IDS = ["SOTA-001", "SOTA-002"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, tolerance: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 12.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "12" and payload["mode"] == "full", "Nieprawidlowy wynik Etapu 12.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejnosc Etapu 12.")
    require(payload["historical_code_modified"] is False, "Zmieniono historyczne listingi.")
    for experiment_id in IDS:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS" and row["return_code"] == 0, f"Blad wykonania {experiment_id}.")
        require(row["source_code_level"] == "FULL_SOURCE", f"Bledna granica zrodlowa {experiment_id}.")
        require(row["historical_code_modified"] is False, f"Zmieniono zrodlo {experiment_id}.")
        comparison = row["comparison"]
        require(comparison["status"] == "CONCLUSION_MATCH", f"Bledny status {experiment_id}.")
        require(comparison["architecture_contract_status"] == "EXACT_MATCH", f"Bledny kontrakt {experiment_id}.")
        require(comparison["scientific_conclusion_preserved"] is True, f"Nie zachowano wniosku {experiment_id}.")
        stderr = (RUN / row["stderr_file"]).read_text(encoding="utf-8", errors="replace").lower()
        require("traceback" not in stderr and "runtimeerror" not in stderr, f"Blad zapisany w stderr {experiment_id}.")

    first = payload["experiments"]["SOTA-001"]["comparison"]
    require(close(first["max_accuracy_delta_pp"], 12.0), "Bledna roznica SOTA-001.")
    require(close(first["accuracy_deltas_pp"]["MLP"], 6.2), "Bledna roznica MLP.")
    require(close(first["accuracy_deltas_pp"]["Fractal_SBOHN_v2"], 12.0), "Bledna roznica SBOHN.")
    accuracy = json.loads((RUN / "raw" / "SOTA-001_historical_result.json").read_text(encoding="utf-8"))
    expected_params = {"MLP": 235146, "ViT-Tiny": 71946, "Fractal_SBOHN_v2": 54298, "CNN": 23946}
    for name, expected in expected_params.items():
        require(accuracy[name]["params"] == expected, f"Bledna liczba parametrow {name}.")
    ranking = sorted(expected_params, key=lambda name: accuracy[name]["acc"], reverse=True)
    require(ranking == ["MLP", "ViT-Tiny", "Fractal_SBOHN_v2", "CNN"], "Nie zachowano rankingu SOTA-001.")
    require(close(accuracy["Fractal_SBOHN_v2"]["acc"], 66.2), "Zmieniono wynik SBOHN.")

    second = payload["experiments"]["SOTA-002"]["comparison"]
    require(close(second["max_timing_delta_ms"], 17.05, 1e-8), "Bledna roznica czasu SOTA-002.")
    require(close(second["max_scaling_exponent_delta"], 0.069, 1e-8), "Bledna roznica wykladnika.")
    scaling = json.loads((RUN / "raw" / "SOTA-002_historical_result.json").read_text(encoding="utf-8"))
    require(close(scaling["Fractal_SBOHN_v2"]["scaling_exp"], -0.010), "Zmieniono wykladnik SBOHN.")
    require(close(scaling["CNN"]["scaling_exp"], 0.697), "Zmieniono wykladnik CNN.")
    require(close(scaling["ViT-Tiny"]["scaling_exp"], 0.043), "Zmieniono wykladnik ViT.")
    require(scaling["Fractal_SBOHN_v2"]["scaling_exp"] < scaling["CNN"]["scaling_exp"], "Nie zachowano skalowania SBOHN.")
    require(scaling["ViT-Tiny"]["scaling_exp"] < scaling["CNN"]["scaling_exp"], "Nie zachowano skalowania ViT.")
    return payload


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczna liczbe jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 89, "Nieprawidlowa liczba zakonczonych jednostek.")
    for experiment_id in IDS:
        require(by_id[experiment_id]["reproduction_status"] == "CONCLUSION_MATCH", f"Bledny inwentarz {experiment_id}.")
        require(by_id[experiment_id]["source_code_level"] == "FULL", f"Bledny poziom kodu {experiment_id}.")
    return len(rows), len(completed)


def validate_documentation() -> None:
    analysis = (ROOT / "docs" / "STAGE_12_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("66,2" in analysis and "+12,0" in analysis, "Brak interpretacji SOTA-001.")
    require("17,05 ms" in analysis and "89 ze 115" in analysis, "Brak interpretacji SOTA-002 lub pokrycia.")
    latest = (ROOT / "reproduced" / "stage_12_runs" / "LATEST_RUN.txt").read_text(encoding="utf-8").strip()
    require(latest == "reproduced/stage_12_runs/20260927T184235Z", "Bledny wskaznik LATEST_RUN.")


def main() -> int:
    validate_manifest()
    validate_results()
    original, completed = validate_inventory()
    validate_documentation()
    print(
        "STAGE 12 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        "executed=2/2 | architecture_exact=2/2 | conclusions_preserved=2/2 | "
        "SOTA-001_delta_pp=12.0_positive | SOTA-002_max_timing_delta_ms=17.05"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
