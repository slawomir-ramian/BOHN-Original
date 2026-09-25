#!/usr/bin/env python3
"""Walidacja closeoutu eksperymentu uzupełniającego ASD-001R."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "reproduced" / "stage_06_asd_001r_full" / "LATEST_RUN.txt"
PROTOCOL = (
    ROOT
    / "experiments"
    / "04_symmetry_discovery"
    / "ASD-001"
    / "reconstruction"
    / "two_symmetry_protocol.py"
)
LOCK = PROTOCOL.parent / "ASD-001R_PROTOCOL_LOCK.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_manifest(result_dir):
    manifest = result_dir / "MANIFEST_SHA256.txt"
    require(manifest.exists(), "Brak manifestu wyniku ASD-001R.")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = result_dir / relative
        require(path.exists(), f"Brak pliku z manifestu: {relative}")
        require(digest(path) == expected, f"Niezgodny SHA-256: {relative}")


def validate():
    require(LATEST.exists(), "Brak LATEST_RUN.txt dla ASD-001R FULL.")
    relative = LATEST.read_text(encoding="utf-8").strip()
    result_dir = ROOT / relative
    require(result_dir.is_dir(), "Katalog wyniku ASD-001R FULL nie istnieje.")
    validate_manifest(result_dir)

    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    require(digest(PROTOCOL) == lock["protocol_sha256"], "Zmieniono zamrożony protokół.")
    payload = json.loads((result_dir / "results.json").read_text(encoding="utf-8"))
    comparison = payload["comparison"]
    require(payload["experiment_id"] == "ASD-001R", "Nieprawidłowe ID wyniku.")
    require(
        payload["relationship_to_original"] == "PARALLEL_SUPPLEMENTARY_EXPERIMENT",
        "Nieprawidłowa relacja wyniku do ASD-001.",
    )
    require(
        comparison["grade"] == "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        "Brak potwierdzenia strukturalnego.",
    )
    require(comparison["completed_fits"] == 40, "Nie ukończono 40 dopasowań.")
    require(comparison["table_structure_reproduced"], "Nie odtworzono struktury tabeli.")
    require(not comparison["historical_exact_reproduction"], "Błędna kwalifikacja historyczna.")
    require(
        comparison["numeric_comparison"] == "DIFFERENCE_AFTER_CORRECTION",
        "Nie zapisano różnicy numerycznej.",
    )
    require(len(payload["tasks"]) == 40, "Nieprawidłowa liczba rekordów zadań.")
    require(not payload["warning_counts"], "Wynik zawiera ostrzeżenia solvera.")
    for key, task in payload["tasks"].items():
        require(sorted(task["true_ranks"].values()) == [1, 2], f"Błędne rangi: {key}")
        require(
            task["min_true_margin_over_best_random"] > 0,
            f"Brak dodatniego marginesu: {key}",
        )
        require(len(task["candidate_order"]) == 99, f"Błędna liczba kandydatów: {key}")
        require(
            task["oracle_ablation"]["accuracy"]["combined_gain"] > 0,
            f"Kontrola ablacyjna niezaliczona: {key}",
        )

    with (ROOT / "inventory" / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        original = list(csv.DictReader(stream))
    require(len(original) == 115, "Zmieniono kanoniczną liczbę 115 jednostek.")
    require("ASD-001R" not in {row["id"] for row in original}, "ASD-001R trafił do rejestru PDF-a.")
    with (ROOT / "inventory" / "supplementary_experiments.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        supplementary = list(csv.DictReader(stream))
    require(len(supplementary) == 1, "Nieprawidłowy rejestr uzupełniający.")
    require(
        supplementary[0]["reproduction_status"] == "STRUCTURAL_RECONSTRUCTION_CONFIRMED",
        "Nieprawidłowy status w rejestrze uzupełniającym.",
    )
    return {
        "result_dir": relative,
        "fits": 40,
        "grade": comparison["grade"],
        "original_inventory_rows": len(original),
        "supplementary_inventory_rows": len(supplementary),
    }


def main():
    result = validate()
    print(
        f"ASD-001R CLOSEOUT VALIDATION: PASS | {result['grade']} | "
        f"fits={result['fits']} | original={result['original_inventory_rows']} | "
        f"supplementary={result['supplementary_inventory_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
