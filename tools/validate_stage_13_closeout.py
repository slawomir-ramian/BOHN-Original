#!/usr/bin/env python3
"""Walidacja uczciwego closeoutu Etapu 13."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_13_runs" / "20260928T051822Z"
IDS = ["SYS-001", "SYS-002", "SYS-003", "SYS-004", "SYS-005",
       "CPU-001", "CPU-002", "CPU-003", "CPU-004", "CPU-005"]
CPU_STATUS = {
    "CPU-001": ("NUMERIC_DIFFERENCE", False, 3.2),
    "CPU-002": ("CONCLUSION_MATCH", True, 83.4),
    "CPU-003": ("NUMERIC_DIFFERENCE", False, 92.8),
    "CPU-004": ("CONCLUSION_MATCH", True, 55.4),
    "CPU-005": ("CONCLUSION_MATCH", True, 17.2),
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
    require(manifest.is_file(), "Brak manifestu Etapu 13.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "13" and payload["mode"] == "full", "Nieprawidlowy wynik Etapu 13.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejnosc Etapu 13.")
    require(payload["historical_code_modified"] is False, "Zmieniono historyczne listingi.")
    for experiment_id in IDS[:5]:
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS", f"Blad audytu {experiment_id}.")
        require(row["source_boundary"] == "SOURCE_FRAGMENT_ONLY", f"Bledna granica {experiment_id}.")
        require(row["comparison"]["status"] == "AUDITED_REPORTED_RESULT", f"Bledny status {experiment_id}.")
    for experiment_id, expected in CPU_STATUS.items():
        row = payload["experiments"][experiment_id]
        require(row["execution_status"] == "PASS" and row["return_code"] == 0, f"Blad wykonania {experiment_id}.")
        require(row["source_boundary"] == "FULL_SHARED_LISTING", f"Bledna granica {experiment_id}.")
        require(row["historical_code_modified"] is False, f"Zmieniono zrodlo {experiment_id}.")
        comparison = row["comparison"]
        require(comparison["status"] == expected[0], f"Bledny status {experiment_id}.")
        require(comparison["scientific_conclusion_preserved"] is expected[1], f"Bledny wniosek {experiment_id}.")
        require(close(comparison["max_reported_numeric_delta_pp"], expected[2]), f"Bledna delta {experiment_id}.")
        stderr = (RUN / row["stderr_file"]).read_text(encoding="utf-8", errors="replace").lower()
        require("traceback" not in stderr and "runtimeerror" not in stderr, f"Blad zapisany w stderr {experiment_id}.")
    return payload


def validate_raw_results() -> None:
    raw = RUN / "raw"
    first = json.loads((raw / "CPU-001_result.json").read_text(encoding="utf-8"))
    require(first["Deep"]["MNIST"] > first["Shallow"]["MNIST"], "CPU-001 MNIST zmieniony.")
    require(first["Deep"]["Fashion"] < first["Shallow"]["Fashion"], "CPU-001 Fashion nie zapisuje rozbieznosci.")
    require(first["Deep"]["CIFAR10"] > first["Shallow"]["CIFAR10"], "CPU-001 CIFAR10 zmieniony.")
    second = json.loads((raw / "CPU-002_result.json").read_text(encoding="utf-8"))
    require(second["routing"]["MNIST"] == [0.0, 100.0, 0.0, 0.0], "CPU-002 routing MNIST zmieniony.")
    require(second["routing"]["Fashion"] == [0.0, 100.0, 0.0, 0.0], "CPU-002 routing Fashion zmieniony.")
    third = json.loads((raw / "CPU-003_result.json").read_text(encoding="utf-8"))
    require(close(third["MNIST"]["delta"], 0.6) and close(third["Fashion"]["delta"], 37.4), "CPU-003 zmieniony.")
    fourth = json.loads((raw / "CPU-004_result.json").read_text(encoding="utf-8"))
    require(fourth["1000"]["+Last2"]["fashion"] > fourth["1000"]["Frozen"]["fashion"], "CPU-004 adaptacja zmieniona.")
    require(fourth["1000"]["Frozen"]["mnist"] > fourth["1000"]["+Last2"]["mnist"], "CPU-004 retencja zmieniona.")
    fifth = json.loads((raw / "CPU-005_result.json").read_text(encoding="utf-8"))
    require(max(fifth.values()) < 50 and fifth["5000"] > fifth["10"], "CPU-005 wniosek zmieniony.")


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczna liczbe jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 99, "Nieprawidlowa liczba zakonczonych jednostek.")
    for experiment_id in IDS[:5]:
        require(by_id[experiment_id]["source_code_level"] == "SOURCE_FRAGMENT_ONLY", f"Bledny poziom {experiment_id}.")
        require(by_id[experiment_id]["reproduction_status"] == "AUDITED_REPORTED_RESULT", f"Bledny inwentarz {experiment_id}.")
    for experiment_id, expected in CPU_STATUS.items():
        require(by_id[experiment_id]["source_code_level"] == "FULL_SHARED_LISTING", f"Bledny poziom {experiment_id}.")
        require(by_id[experiment_id]["reproduction_status"] == expected[0], f"Bledny inwentarz {experiment_id}.")
    return len(rows), len(completed)


def validate_documentation() -> None:
    analysis = (ROOT / "docs" / "STAGE_13_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("3 z 5" in analysis and "PARTIAL_REPRODUCTION" in analysis, "Brak uczciwej oceny Etapu 13.")
    require("83,4 pp" in analysis and "92,8" not in analysis, "Brak interpretacji routingu lub bledna dokumentacja.")
    require("99 ze 115" in analysis and "16" in analysis, "Brak pokrycia Etapu 13.")
    latest = (ROOT / "reproduced" / "stage_13_runs" / "LATEST_RUN.txt").read_text(encoding="utf-8").strip()
    require(latest == "reproduced/stage_13_runs/20260928T051822Z", "Bledny wskaznik LATEST_RUN.")


def main() -> int:
    validate_manifest()
    validate_results()
    validate_raw_results()
    original, completed = validate_inventory()
    validate_documentation()
    print(
        "STAGE 13 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        "audited_only=5 | executed=5/5 | conclusions_preserved=3/5 | "
        "numeric_difference=2 | grade=PARTIAL_REPRODUCTION"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
