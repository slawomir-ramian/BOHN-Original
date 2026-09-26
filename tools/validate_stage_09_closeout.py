#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 09."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_09_runs" / "20260926T194522Z"
IDS = [
    "FR-001", "FR-004", "FR-002", "FR-003", "PT-001", "PT-002",
    "PT-003", "PT-004", "PT-005", "HR-001", "HR-002", "HR-003",
    "HR-004", "HR-005", "HR-006", "HR-007",
]
AUDITED = {
    "FR-001", "FR-004", "PT-003", "HR-001", "HR-002", "HR-003",
    "HR-004", "HR-005", "HR-006", "HR-007",
}
RUNNABLE = set(IDS) - AUDITED


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 09.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "09" and payload["mode"] == "full", "Nieprawidłowy wynik Etapu 09.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejność Etapu 09.")
    boundary = payload["source_boundary"]
    require(boundary["executable_units"] == 6, "Nieprawidłowa liczba jednostek wykonywalnych.")
    require(boundary["shared_programs"] == 2, "Nieprawidłowa liczba wspólnych programów.")
    require(set(boundary["audited_only"]) == AUDITED, "Błędna granica źródłowa Etapu 09.")
    for experiment_id in IDS:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Błąd wykonania {experiment_id}.")
        require(row["stderr_nonempty"] is False, f"Nieoczekiwany stderr {experiment_id}.")
        stderr = RUN / row["stderr_file"]
        require(stderr.is_file() and stderr.read_bytes() == b"", f"Niepusty plik stderr {experiment_id}.")
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(row["comparison"]["status"] == expected, f"Błędny status {experiment_id}.")
        if experiment_id in RUNNABLE:
            comparison = row["comparison"]
            require(comparison["scientific_conclusion_preserved"] is True, f"Nie zachowano wniosku {experiment_id}.")
            require(comparison["max_reported_numeric_delta"] <= 1e-6, f"Zbyt duża różnica {experiment_id}.")
    require(payload["environment"]["torch"] == "2.14.0+cpu", "Niezgodna wersja PyTorch.")
    return payload


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczną liczbę 115 jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 72, "Nieprawidłowa liczba zakończonych jednostek PDF.")
    for experiment_id in IDS:
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(by_id[experiment_id]["reproduction_status"] == expected, f"Błędny inwentarz {experiment_id}.")
    for experiment_id in {"FR-001", "FR-004"}:
        require(
            by_id[experiment_id]["source_code_level"] == "CHAPTER_NARRATIVE_TARGET_CODE_ABSENT",
            f"Ukryto granicę źródła {experiment_id}.",
        )
    require(
        by_id["PT-003"]["source_code_level"] == "SHARED_LISTING_TARGET_CODE_ABSENT",
        "Ukryto granicę źródła PT-003.",
    )
    for experiment_id in {f"HR-{number:03d}" for number in range(1, 8)}:
        require(by_id[experiment_id]["source_code_level"] == "NARRATIVE_ONLY", f"Błędna granica {experiment_id}.")
    return len(rows), len(completed)


def main() -> int:
    validate_manifest()
    payload = validate_results()
    original, completed = validate_inventory()
    maximum = max(
        payload["experiments"][experiment_id]["comparison"]["max_reported_numeric_delta"]
        for experiment_id in RUNNABLE
    )
    print(
        "STAGE 09 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        f"runnable_close_match={len(RUNNABLE)}/6 | max_delta={maximum:.10f} | audited_only={len(AUDITED)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
