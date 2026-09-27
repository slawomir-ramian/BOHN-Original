#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 10."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_10_runs" / "20260926T211342Z"
IDS = [f"MS-{number:03d}" for number in range(1, 11)]
AUDITED = set(IDS[:8])
RUNNABLE = {"MS-009", "MS-010"}
FRAGMENTS = {"MS-005", "MS-006", "MS-007", "MS-008"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 10.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "10" and payload["mode"] == "full", "Nieprawidłowy wynik Etapu 10.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejność Etapu 10.")
    boundary = payload["source_boundary"]
    require(boundary["executable_units"] == 2 and boundary["shared_programs"] == 1, "Błędna granica programu.")
    require(set(boundary["source_fragment_only"]) == FRAGMENTS, "Błędna granica fragmentów.")
    require(set(boundary["narrative_only"]) == set(IDS[:4]), "Błędna granica narracji.")

    for experiment_id in IDS:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Błąd wykonania {experiment_id}.")
        require(row["stderr_nonempty"] is False, f"Nieoczekiwany stderr {experiment_id}.")
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(row["comparison"]["status"] == expected, f"Błędny status {experiment_id}.")
    require(payload["experiments"]["MS-009"]["comparison"]["scientific_conclusion_preserved"] is True, "Nie zachowano wniosku MS-009.")
    require(payload["experiments"]["MS-010"]["comparison"]["scientific_conclusion_preserved"] is True, "Nie zachowano wniosku MS-010.")
    require(payload["experiments"]["MS-009"]["comparison"]["max_reported_numeric_delta"] <= 0.0032, "Zbyt duża różnica MS-009.")
    require(payload["experiments"]["MS-010"]["comparison"]["max_reported_numeric_delta"] <= 0.0102, "Zbyt duża różnica MS-010.")

    historical = json.loads((RUN / "raw" / "MS-009_historical_result.json").read_text(encoding="utf-8"))
    require(historical["protocol"]["expected_cells"] == 180, "Niepełny protokół historyczny.")
    require(len(historical["rows"]) == 180, "Niepełna liczba komórek.")
    unique = {(int(row["seed"]), row["task"], row["mode"]) for row in historical["rows"]}
    require(len(unique) == 180, "Powtórzone lub brakujące komórki.")
    summary = historical["summary"]
    require(abs(summary["annealed_geometry"]["medium"]["acc092_and_sim025"] - 0.15) < 1e-12, "Nie odtworzono basinu medium.")
    require(abs(summary["annealed_geometry"]["hard"]["acc092_and_sim025"] - 0.05) < 1e-12, "Nie odtworzono basinu hard.")
    require(summary["accuracy_only"]["medium"]["acc092_and_sim025"] == 0.0, "Nieoczekiwany basin medium accuracy_only.")
    require(summary["accuracy_only"]["hard"]["acc092_and_sim025"] == 0.0, "Nieoczekiwany basin hard accuracy_only.")

    logs = RUN / "raw" / "MS-009_cell_logs"
    stderr_logs = sorted(logs.glob("*_stderr.txt"))
    stdout_logs = sorted(logs.glob("*_stdout.txt"))
    require(len(stderr_logs) == 180 and len(stdout_logs) == 180, "Brak kompletu logów 180 komórek.")
    require(all(path.stat().st_size == 0 for path in stderr_logs + stdout_logs), "Niepusty log komórki.")
    return payload


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczną liczbę 115 jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 82, "Nieprawidłowa liczba zakończonych jednostek PDF.")
    for experiment_id in IDS:
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(by_id[experiment_id]["reproduction_status"] == expected, f"Błędny inwentarz {experiment_id}.")
    for experiment_id in FRAGMENTS:
        require(by_id[experiment_id]["source_code_level"] == "SOURCE_FRAGMENT_ONLY", f"Ukryto granicę {experiment_id}.")
    for experiment_id in RUNNABLE:
        require(by_id[experiment_id]["source_code_level"] == "FULL_SHARED_LISTING", f"Błędny poziom {experiment_id}.")
    return len(rows), len(completed)


def main() -> int:
    validate_manifest()
    payload = validate_results()
    original, completed = validate_inventory()
    delta9 = payload["experiments"]["MS-009"]["comparison"]["max_reported_numeric_delta"]
    delta10 = payload["experiments"]["MS-010"]["comparison"]["max_reported_numeric_delta"]
    print(
        "STAGE 10 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        f"cells=180/180 | close_match=2/2 | max_delta_v5={delta9:.7f} | "
        f"max_delta_v6={delta10:.7f} | audited_only=8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
