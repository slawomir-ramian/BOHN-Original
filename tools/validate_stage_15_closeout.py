#!/usr/bin/env python3
"""Walidacja uczciwego closeoutu Etapu 15 i pełnego pokrycia 115/115."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_15_runs" / "20260928T185044Z"
IDS = ["RF-001", "RF-002", "MF-001", "MF-002", "MF-003", "MF-004", "MF-005"]
STATUSES = {
    "RF-001": ("CLOSE_NUMERIC_MATCH", True),
    "RF-002": ("CLOSE_NUMERIC_MATCH", True),
    "MF-001": ("CLOSE_NUMERIC_MATCH", True),
    "MF-002": ("CLOSE_NUMERIC_MATCH", True),
    "MF-003": ("CONCLUSION_MATCH", True),
    "MF-004": ("CONCLUSION_MATCH", True),
    "MF-005": ("NUMERIC_DIFFERENCE", False),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(first: float, second: float, tolerance: float = 1e-9) -> bool:
    return abs(float(first) - float(second)) <= tolerance


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 15.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "15" and payload["mode"] == "full", "Nieprawidlowy wynik Etapu 15.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejnosc Etapu 15.")
    require(payload["historical_code_modified"] is False, "Zmieniono historyczny listing 71.")
    for experiment_id, (status, preserved) in STATUSES.items():
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS" and row["return_code"] == 0, f"Blad wykonania {experiment_id}.")
        require(row["source_boundary"] == "FULL_SUITE", f"Bledna granica {experiment_id}.")
        require(row["historical_code_modified"] is False, f"Zmieniono zrodlo {experiment_id}.")
        require(row["comparison"]["status"] == status, f"Bledny status {experiment_id}.")
        require(row["comparison"]["scientific_conclusion_preserved"] is preserved,
                f"Bledna flaga wniosku {experiment_id}.")
    mf5 = payload["experiments"]["MF-005"]["comparison"]
    require(mf5["wins_over_fbohn"] == 39 and mf5["top_operator"] == "mul", "Zmieniono wynik MF-005.")
    require(close(mf5["aunc"]["Meta-FBOHN-v5-library"], 0.6541111111111111), "Zmieniono AUNC v5.")
    require(close(mf5["max_reported_numeric_delta_pp"], 0.13111111111110407), "Zmieniono delte MF-005.")
    return payload


def validate_mf5_raw() -> None:
    payload = json.loads((RUN / "raw" / "MF-005_result.json").read_text(encoding="utf-8"))
    rows = {(float(row["noise"]), int(row["seed"]), row["representation"]): float(row["accuracy"])
            for row in payload["rows"]}
    noises = [0.0, 0.1, 0.3, 0.5]
    v5 = "Meta-FBOHN-v5-library"
    wins_fbohn = sum(rows[(noise, seed, v5)] > rows[(noise, seed, "FBOHN")]
                      for noise in noises for seed in range(10))
    wins_poly = sum(rows[(noise, seed, v5)] > rows[(noise, seed, "FBOHN-poly-control")]
                    for noise in noises for seed in range(10))
    require(wins_fbohn == 39 and wins_poly == 40, "Zmieniono liczbe zwyciestw MF-005.")
    require(close(rows[(0.5, 4, v5)], 0.6294444444444445), "Zmieniono wyjatek MF-005.")
    require(close(rows[(0.5, 4, "FBOHN")], 0.63), "Zmieniono FBOHN dla wyjatku MF-005.")
    require(next(iter(payload["operator_counts"])) == "mul" and payload["operator_counts"]["mul"] == 824,
            "Zmieniono dominujacy operator.")


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczna liczbe jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 115, "Repozytorium nie osiagnelo 115/115.")
    for experiment_id, (status, _) in STATUSES.items():
        require(by_id[experiment_id]["source_code_level"] == "FULL_SUITE", f"Bledny poziom {experiment_id}.")
        require(by_id[experiment_id]["reproduction_status"] == status, f"Bledny inwentarz {experiment_id}.")
    return len(rows), len(completed)


def validate_documentation() -> None:
    analysis = (ROOT / "docs" / "STAGE_15_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("115 ze 115" in analysis and "39/40" in analysis and "40/40" in analysis,
            "Brak uczciwego podsumowania Etapu 15.")
    require("−0,0556 pp" in analysis and "NEAR_COMPLETE_REPRODUCTION" in analysis,
            "Brak interpretacji MF-005.")
    latest = (ROOT / "reproduced" / "stage_15_runs" / "LATEST_RUN.txt").read_text(encoding="utf-8").strip()
    require(latest == "reproduced/stage_15_runs/20260928T185044Z", "Bledny wskaznik LATEST_RUN.")


def main() -> int:
    validate_manifest()
    validate_results()
    validate_mf5_raw()
    original, completed = validate_inventory()
    validate_documentation()
    print(
        "STAGE 15 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        "executed=7/7 | strict_conclusions_preserved=6/7 | main_mechanisms_preserved=7/7 | "
        "MF-005_FBOHN_wins=39/40 | MF-005_poly_wins=40/40 | grade=NEAR_COMPLETE_REPRODUCTION"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
