#!/usr/bin/env python3
"""Walidacja uczciwego closeoutu Etapu 14."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_14_runs" / "20260928T180446Z"
IDS = ["MOE-001", "MOE-009", "MOE-002", "MOE-003", "MOE-004",
       "MOE-005", "MOE-006", "MOE-007", "MOE-008"]
AUDIT_IDS = ["MOE-001", "MOE-009", "MOE-002", "MOE-003", "MOE-005", "MOE-007"]
EXECUTED = {
    "MOE-004": ("FULL", "NUMERIC_DIFFERENCE", False, 42.0),
    "MOE-006": ("FULL_SHARED_LISTING", "CONCLUSION_MATCH", True, 10.7),
    "MOE-008": ("FULL", "NUMERIC_DIFFERENCE", False, 62.2),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, tolerance: float = 1e-8) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 14.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "14" and payload["mode"] == "full", "Nieprawidlowy wynik Etapu 14.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejnosc Etapu 14.")
    require(payload["historical_code_modified"] is False, "Zmieniono historyczne listingi.")
    for experiment_id in AUDIT_IDS:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Blad audytu {experiment_id}.")
        require(row["comparison"]["status"] == "AUDITED_REPORTED_RESULT", f"Bledny status {experiment_id}.")
    for experiment_id, expected in EXECUTED.items():
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS" and row["return_code"] == 0, f"Blad wykonania {experiment_id}.")
        require(row["source_boundary"] == expected[0], f"Bledna granica {experiment_id}.")
        require(row["historical_code_modified"] is False, f"Zmieniono zrodlo {experiment_id}.")
        comparison = row["comparison"]
        require(comparison["status"] == expected[1], f"Bledny status {experiment_id}.")
        require(comparison["scientific_conclusion_preserved"] is expected[2], f"Bledny wniosek {experiment_id}.")
        require(close(comparison["max_reported_numeric_delta_pp"], expected[3]), f"Bledna delta {experiment_id}.")
        stderr = (RUN / row["stderr_file"]).read_text(encoding="utf-8", errors="replace").lower()
        require("traceback" not in stderr and "runtimeerror" not in stderr, f"Blad w stderr {experiment_id}.")
    return payload


def validate_raw_results() -> None:
    raw = RUN / "raw"
    hard = json.loads((raw / "MOE-004_result.json").read_text(encoding="utf-8"))
    require(close(hard["MNIST"]["accuracy"], 65.0), "MOE-004 MNIST zmieniony.")
    require(hard["MNIST"]["gate"] == [57.8, 0.0, 42.2, 0.0], "MOE-004 routing zmieniony.")
    require(hard["KMNIST"]["gate"][2] == 98.8, "MOE-004 KMNIST zmieniony.")

    confidence = json.loads((raw / "MOE-006_result.json").read_text(encoding="utf-8"))
    averages = {
        method: sum(rows[domain]["accuracy"] for domain in ["MNIST", "Fashion", "KMNIST"]) / 3
        for method, rows in confidence["methods"].items()
    }
    require(averages["max_logit"] > averages["confidence"] > averages["margin"], "MOE-006 ranking zmieniony.")

    hybrid = json.loads((raw / "MOE-008_result.json").read_text(encoding="utf-8"))
    require(close(hybrid["avg_gated"], 63.5) and close(hybrid["avg_oracle"], 88.4), "MOE-008 srednie zmienione.")
    require(close(hybrid["forgetting"], 0.0) and close(hybrid["gate_overhead"], 24.9), "MOE-008 kontrakt zmieniony.")
    require(hybrid["domains"]["MNIST"]["gate"] == [37.8, 0.0, 62.2, 0.0], "MOE-008 routing zmieniony.")


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczna liczbe jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 108, "Nieprawidlowa liczba zakonczonych jednostek.")
    for experiment_id in AUDIT_IDS:
        require(by_id[experiment_id]["reproduction_status"] == "AUDITED_REPORTED_RESULT", f"Bledny inwentarz {experiment_id}.")
    for experiment_id, expected in EXECUTED.items():
        require(by_id[experiment_id]["source_code_level"] == expected[0], f"Bledny poziom {experiment_id}.")
        require(by_id[experiment_id]["reproduction_status"] == expected[1], f"Bledny inwentarz {experiment_id}.")
    return len(rows), len(completed)


def validate_documentation() -> None:
    analysis = (ROOT / "docs" / "STAGE_14_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("1 z 3" in analysis and "PARTIAL_REPRODUCTION" in analysis, "Brak uczciwej oceny Etapu 14.")
    require("63,5%" in analysis and "88,4%" in analysis and "24,9%" in analysis, "Brak interpretacji MOE-008.")
    require("108 ze 115" in analysis and "7" in analysis, "Brak pokrycia Etapu 14.")
    latest = (ROOT / "reproduced" / "stage_14_runs" / "LATEST_RUN.txt").read_text(encoding="utf-8").strip()
    require(latest == "reproduced/stage_14_runs/20260928T180446Z", "Bledny wskaznik LATEST_RUN.")


def main() -> int:
    validate_manifest()
    validate_results()
    validate_raw_results()
    original, completed = validate_inventory()
    validate_documentation()
    print(
        "STAGE 14 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        "audited_only=6 | executed=3/3 | conclusions_preserved=1/3 | "
        "numeric_difference=2 | grade=PARTIAL_REPRODUCTION"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
