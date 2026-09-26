#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 08."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_08_runs" / "20260926T181227Z"
IDS = ["LS-001", "LS-002", "LS-003", "LS-004", "LS-005", "LS-006", "LD-001", "LD-002", "LD-003", "LD-004", "LD-005"]
AUDITED = {"LS-002", "LS-003", "LS-004", "LS-005", "LS-006"}
RUNNABLE = set(IDS) - AUDITED


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 08.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "08" and payload["mode"] == "full", "Nieprawidlowy wynik Etapu 08.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejnosc Etapu 08.")
    require(set(payload["source_boundary"]["target_code_absent_for"]) == AUDITED, "Bledna granica listingu 53.")
    for experiment_id in IDS:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Blad wykonania {experiment_id}.")
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(row["comparison"]["status"] == expected, f"Bledny status {experiment_id}.")
        if experiment_id in RUNNABLE:
            require(row["comparison"]["scientific_conclusion_preserved"] is True, f"Nie zachowano wniosku {experiment_id}.")
            require(row["comparison"]["max_reported_numeric_delta"] <= 0.003, f"Zbyt duza roznica {experiment_id}.")
    warning = (RUN / "raw" / "LD-001_stderr.txt").read_text(encoding="utf-8")
    require("UserWarning" in warning and "requires_grad=True" in warning, "Nieoczekiwany stderr LD-001.")
    require(payload["environment"]["torch"] == "2.14.0+cpu", "Niezgodna wersja PyTorch.")
    return payload


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczna liczbe 115 jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 56, "Nieprawidlowa liczba zakonczonych jednostek PDF.")
    for experiment_id in IDS:
        expected = "AUDITED_REPORTED_RESULT" if experiment_id in AUDITED else "CLOSE_NUMERIC_MATCH"
        require(by_id[experiment_id]["reproduction_status"] == expected, f"Bledny inwentarz {experiment_id}.")
    for experiment_id in AUDITED:
        require(by_id[experiment_id]["source_code_level"] == "SHARED_LISTING_TARGET_CODE_ABSENT", f"Ukryto granice zrodla {experiment_id}.")
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
        "STAGE 08 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        f"runnable_close_match={len(RUNNABLE)}/6 | max_delta={maximum:.7f} | audited_only=5"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
