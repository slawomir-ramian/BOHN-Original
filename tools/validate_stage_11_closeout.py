#!/usr/bin/env python3
"""Walidacja closeoutu Etapu 11 z jawnym wynikiem mieszanym."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reproduced" / "stage_11_runs" / "20260927T161144Z"
IDS = ["AD-001", "AD-002", "AD-003", "CL-001", "CL-002"]
EXPECTED = {
    "AD-001": ("NUMERIC_DIFFERENCE", False, 29.8),
    "AD-002": ("CONCLUSION_MATCH", True, 38.31),
    "AD-003": ("CONCLUSION_MATCH", True, 23.7),
    "CL-001": ("CLOSE_NUMERIC_MATCH", True, 3.3),
    "CL-002": ("CONCLUSION_MATCH", True, 16.34),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, tolerance: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def validate_manifest() -> None:
    manifest = RUN / "MANIFEST_SHA256.txt"
    require(manifest.is_file(), "Brak manifestu Etapu 11.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = RUN / relative
        require(path.is_file(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate_results() -> dict:
    payload = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == "11" and payload["mode"] == "full", "Nieprawidłowy wynik Etapu 11.")
    require(payload["source_chronology"] == IDS, "Zmieniono kolejność Etapu 11.")

    for experiment_id in IDS:
        row = payload["experiments"][experiment_id]
        status, conclusion, delta = EXPECTED[experiment_id]
        require(row["execution_status"] == "PASS" and row["return_code"] == 0, f"Błąd wykonania {experiment_id}.")
        require(row["source_boundary"] == "SOURCE_FRAGMENT_ONLY", f"Ukryto granicę źródłową {experiment_id}.")
        require(row["historical_code_modified"] is False, f"Zmieniono źródło historyczne {experiment_id}.")
        require(row["reconstruction_is_historical_source"] is False, f"Rekonstrukcja udaje źródło {experiment_id}.")
        comparison = row["comparison"]
        require(comparison["status"] == status, f"Błędny status {experiment_id}.")
        require(comparison["scientific_conclusion_preserved"] is conclusion, f"Błędna ocena wniosku {experiment_id}.")
        require(close(comparison["max_reported_numeric_delta_pp"], delta, 1e-8), f"Błędna różnica {experiment_id}.")
        stderr = (RUN / row["stderr_file"]).read_text(encoding="utf-8", errors="replace").lower()
        require("traceback" not in stderr and "runtimeerror" not in stderr, f"Błąd zapisany w stderr {experiment_id}.")

    hashes = {experiment_id: payload["experiments"][experiment_id]["reconstruction_result_sha256"] for experiment_id in IDS}
    require(hashes["AD-001"] == hashes["CL-001"], "Jednostki listingu 58 nie dzielą wyniku.")
    require(hashes["AD-002"] == hashes["AD-003"] == hashes["CL-002"], "Jednostki listingu 59 nie dzielą wyniku.")

    first = json.loads((RUN / "raw" / "AD-001_reconstruction_result.json").read_text(encoding="utf-8"))
    require(first["protocol"] == "STAGE_11_RECONSTRUCTION_V1", "Błędny protokół rekonstrukcji.")
    require(close(first["fewshot"]["500"]["perm_head"], 21.6), "Zmieniono wynik AD-001 Perm+Head.")
    require(close(first["fewshot"]["500"]["head_only"], 22.3), "Zmieniono wynik AD-001 Head only.")
    require(close(first["continual"]["sbohn_mnist_degradation"], 0.0), "Nie odtworzono restore CL-001.")
    require(first["continual"]["mlp_mnist_degradation"] > 0.0, "Brak kontroli forgetting CL-001.")

    second = json.loads((RUN / "raw" / "AD-002_reconstruction_result.json").read_text(encoding="utf-8"))
    require(close(second["fewshot"]["500"]["sbohn_head_only"], 48.33), "Zmieniono wynik AD-003 Head only.")
    require(close(second["fewshot"]["500"]["sbohn_full_tune"], 50.70), "Zmieniono wynik AD-003 Full tune.")
    require(second["fewshot"]["500"]["sbohn_head_only"] >= 0.85 * second["fewshot"]["500"]["sbohn_full_tune"], "Nie zachowano modularności AD-003.")
    require(close(second["continual"]["sbohn_mnist_degradation"], 0.0), "Nie odtworzono restore CL-002.")
    require(second["continual"]["mlp_mnist_degradation"] > 0.0, "Brak kontroli forgetting CL-002.")
    return payload


def validate_inventory() -> tuple[int, int]:
    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Zmieniono kanoniczną liczbę 115 jednostek.")
    by_id = {row["id"]: row for row in rows}
    completed = [row for row in rows if row["reproduction_status"] != "NOT_RUN"]
    require(len(completed) == 87, "Nieprawidłowa liczba zakończonych jednostek PDF.")
    for experiment_id, (status, _, _) in EXPECTED.items():
        require(by_id[experiment_id]["reproduction_status"] == status, f"Błędny inwentarz {experiment_id}.")
        require(by_id[experiment_id]["source_code_level"] == "SOURCE_FRAGMENT_ONLY", f"Ukryto fragment źródła {experiment_id}.")
    return len(rows), len(completed)


def validate_documentation() -> None:
    analysis = (ROOT / "docs" / "STAGE_11_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("AD-001" in analysis and "NUMERIC_DIFFERENCE" in analysis, "Analiza nie dokumentuje rozbieżności AD-001.")
    require("29,8 pp" in analysis and "87 ze 115" in analysis, "Analiza nie dokumentuje skali lub pokrycia.")


def main() -> int:
    validate_manifest()
    payload = validate_results()
    original, completed = validate_inventory()
    validate_documentation()
    preserved = sum(bool(payload["experiments"][experiment_id]["comparison"]["scientific_conclusion_preserved"]) for experiment_id in IDS)
    print(
        "STAGE 11 CLOSEOUT VALIDATION: PASS | "
        f"original={original} | completed={completed} | remaining={original-completed} | "
        f"executed=5/5 | conclusions_preserved={preserved}/5 | "
        "close_numeric=1 | conclusion_match=3 | numeric_difference=1 | AD-001_delta_pp=29.8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
