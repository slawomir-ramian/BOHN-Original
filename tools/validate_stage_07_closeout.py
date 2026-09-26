#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 07 i rekonstrukcji uzupełniających 07R."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE7 = ROOT / "reproduced" / "stage_07_runs" / "20260925T222755Z"
STAGE7R = ROOT / "reproduced" / "stage_07r_full" / "20260926T074159Z"
ORIGINAL_IDS = ["PL-001", "PL-002", "PL-003", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001", "HD-002", "HD-003", "CMP-001", "CMP-002"]
SUPPLEMENTARY_IDS = ["PL-002R", "PL-003R", "HD-003R", "CMP-001R", "CMP-002R"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(directory: Path) -> None:
    manifest = directory / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), f"Brak manifestu: {directory}")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = directory / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_stage7() -> dict:
    validate_manifest(STAGE7)
    payload = json.loads((STAGE7 / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "07" and payload["mode"] == "full", "Nieprawidłowy wynik Etapu 07.")
    require(payload["source_chronology"] == ORIGINAL_IDS, "Zmieniono kolejność Etapu 07.")
    expected = {
        "PL-001": "CLOSE_NUMERIC_MATCH",
        "PL-002": "AUDITED_REPORTED_RESULT",
        "PL-003": "AUDITED_REPORTED_RESULT",
        "AR-001": "CLOSE_NUMERIC_MATCH",
        "AR-002": "CONCLUSION_MATCH",
        "AR-003": "CLOSE_NUMERIC_MATCH",
        "AR-004": "CLOSE_NUMERIC_MATCH",
        "HD-001": "CONCLUSION_MATCH",
        "HD-002": "CONCLUSION_MATCH",
        "HD-003": "AUDITED_REPORTED_RESULT",
        "CMP-001": "AUDITED_REPORTED_RESULT",
        "CMP-002": "AUDITED_REPORTED_RESULT",
    }
    for experiment_id, status in expected.items():
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Błąd wykonania {experiment_id}.")
        require(row["comparison"]["status"] == status, f"Błędny status {experiment_id}.")
    return payload


def validate_stage7r() -> dict:
    validate_manifest(STAGE7R)
    payload = json.loads((STAGE7R / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "07R" and payload["mode"] == "full", "Nieprawidłowy wynik Etapu 07R.")
    require(payload["grade"] == "PARTIAL_SUPPLEMENTARY_CONFIRMATION", "Błędny grade Etapu 07R.")
    require(payload["source_order"] == SUPPLEMENTARY_IDS, "Zmieniono kolejność Etapu 07R.")
    expected = {
        "PL-002R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        "PL-003R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        "HD-003R": "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED",
        "CMP-001R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        "CMP-002R": "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
    }
    for experiment_id, status in expected.items():
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Błąd wykonania {experiment_id}.")
        require(row["result"]["status"] == status, f"Błędny status {experiment_id}.")
    hd = payload["experiments"]["HD-003R"]["result"]
    rows = hd["metrics"]["rows"]
    gains = [row["gain"] for row in rows]
    wins = [row["wins"] for row in rows]
    require(all(gain > 0 for gain in gains), "HD-003R nie zachowuje dodatnich średnich gain.")
    require(all(a > b for a, b in zip(gains, gains[1:])), "HD-003R nie zachowuje malejącego trendu.")
    require(wins == [10, 10, 7, 6], "Niezgodne liczby wygranych HD-003R.")
    require(hd["convergence_warning_count"] == 10, "Niezgodna liczba ostrzeżeń HD-003R.")
    cmp2 = payload["experiments"]["CMP-002R"]["result"]["metrics"]
    require(all(value == 10 for value in cmp2["srl_wins_over_pca"].values()), "CMP-002R nie ma 10/10 wygranych.")
    require(cmp2["mean_srl"]["2"] / cmp2["mean_full"] >= 0.90, "CMP-002R nie spełnia progu latentu.")
    return payload


def validate_inventories() -> tuple[int, int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        original = list(csv.DictReader(stream))
    require(len(original) == 115, "Zmieniono kanoniczną liczbę 115 jednostek.")
    completed = [row for row in original if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 45, "Nieprawidłowa liczba zakończonych jednostek PDF.")
    require(not set(SUPPLEMENTARY_IDS) & {row["id"] for row in original}, "Jednostka R trafiła do rejestru PDF-a.")
    with (ROOT / "inventory" / "supplementary_experiments.csv").open(encoding="utf-8", newline="") as stream:
        supplementary = list(csv.DictReader(stream))
    require(len(supplementary) == 6, "Nieprawidłowa liczba eksperymentów uzupełniających.")
    by_id = {row["id"]: row for row in supplementary}
    require(by_id["HD-003R"]["reproduction_status"] == "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED", "Ukryto negatywny wynik HD-003R.")
    require(sum(row["reproduction_status"] == "STRUCTURAL_RECONSTRUCTION_CONFIRMED" for row in supplementary if row["id"] in SUPPLEMENTARY_IDS) == 4, "Nieprawidłowa liczba potwierdzeń 07R.")
    return len(original), len(completed), len(supplementary)


def main() -> int:
    validate_stage7()
    validate_stage7r()
    original, completed, supplementary = validate_inventories()
    print(
        "STAGE 07/07R CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | supplementary={supplementary} | "
        "07R_confirmed=4/5 | grade=PARTIAL_SUPPLEMENTARY_CONFIRMATION"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
