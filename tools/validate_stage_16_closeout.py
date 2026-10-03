#!/usr/bin/env python3
"""Validate the complete Stage 16 supplementary closeout."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HISTORICAL_SHA = "ba576b945052cc70b44dcecaece3bc90eb728787ecf86f9cece1d17217a4b116"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_manifest(run: Path) -> int:
    manifest = run / "MANIFEST_SHA256.txt"
    require(manifest.exists(), "Missing Stage 16 manifest")
    count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = run / relative
        require(target.is_file(), f"Missing manifest entry: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        require(actual == expected, f"SHA-256 mismatch: {relative}")
        count += 1
    require(count == 8, f"Expected 8 manifest entries, got {count}")
    return count


def main() -> int:
    historical = ROOT / "experiments" / "10_sota_and_scaling" / "SOTA-002" / "historical" / "source_from_monograph.py"
    require(historical.exists(), "Missing historical SOTA-002 source")
    require(hashlib.sha256(historical.read_bytes()).hexdigest() == EXPECTED_HISTORICAL_SHA,
            "Historical SOTA-002 source was modified")

    with (ROOT / "inventory" / "experiments.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        canonical = list(csv.DictReader(handle))
    require(len(canonical) == 115, f"Canonical inventory changed: {len(canonical)}")

    with (ROOT / "inventory" / "supplementary_experiments.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        supplementary = {row["id"]: row for row in csv.DictReader(handle)}
    require(len(supplementary) >= 8, f"Expected at least 8 supplementary units, got {len(supplementary)}")
    for unit, status in (("SOTA-002R", "DIRECT_REPLICATION_PASS"), ("SOTA-002H", "STRUCTURAL_FRONTEND_PASS")):
        require(unit in supplementary, f"Missing supplementary unit: {unit}")
        require(supplementary[unit]["parent_id"] == "SOTA-002", f"Wrong parent: {unit}")
        require(supplementary[unit]["relationship_to_pdf"] == "OUTSIDE_115_PDF_CHRONOLOGY",
                f"Wrong chronology boundary: {unit}")
        require(supplementary[unit]["reproduction_status"] == status, f"Wrong status: {unit}")

    latest = (ROOT / "reproduced" / "stage_16_runs" / "LATEST_RUN.txt").read_text(encoding="utf-8").strip()
    run = ROOT / "reproduced" / "stage_16_runs" / latest
    require(latest == "20261003T062344Z", f"Unexpected Stage 16 full run: {latest}")
    manifest_entries = validate_manifest(run)
    payload = json.loads((run / "results.json").read_text(encoding="utf-8"))
    require(payload["stage"] == 16 and payload["mode"] == "FULL" and payload["status"] == "PASS",
            "Stage 16 result header mismatch")
    direct = payload["units"]["SOTA-002R"]
    hierarchical = payload["units"]["SOTA-002H"]
    require(direct["status"] == "DIRECT_REPLICATION_PASS", "SOTA-002R did not pass")
    require(not direct["historical_source_modified"] and not direct["scientific_target_hardcoded"],
            "SOTA-002R provenance boundary failed")
    require(len(direct["rows"]) == 6, "SOTA-002R resolution grid mismatch")
    require(all(row["historical_token_count"] == 16 for row in direct["rows"]), "Historical token count changed")
    require(direct["rows"][-1]["cnn_over_historical_speedup"] > 1.0, "No high-resolution timing advantage")

    require(hierarchical["status"] == "STRUCTURAL_FRONTEND_PASS", "SOTA-002H did not pass")
    require(hierarchical["architecture_claim_only"] and not hierarchical["classification_accuracy_claim"],
            "SOTA-002H claim boundary failed")
    require(not hierarchical["entire_pipeline_o1_claim"], "Invalid end-to-end O(1) claim")
    require(len(hierarchical["rows"]) == 9, "SOTA-002H resolution grid mismatch")
    require({row["parameters"] for row in hierarchical["rows"]} == {51434}, "Parameters are not fixed")
    require({row["token_count"] for row in hierarchical["rows"]} == {16}, "Tokens are not fixed")
    require(all(row["output_finite"] for row in hierarchical["rows"]), "Non-finite SOTA-002H output")

    analysis = (ROOT / "docs" / "STAGE_16_LOCAL_ANALYSIS.md").read_text(encoding="utf-8")
    require("TECHNICAL_CONFIRMATION_WITH_LIMITATIONS" in analysis, "Missing controlled grade")
    require("Nie potwierdzono" in analysis, "Missing limitations section")

    print(
        f"STAGE 16 CLOSEOUT VALIDATION: PASS | canonical=115 | supplementary={len(supplementary)} | "
        f"manifest={manifest_entries}/8 | direct=PASS | hierarchical=PASS | "
        "grade=TECHNICAL_CONFIRMATION_WITH_LIMITATIONS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
