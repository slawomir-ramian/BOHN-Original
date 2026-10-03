#!/usr/bin/env python3
"""Verify the frozen Stage 16 protocol and historical-source boundary."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "experiments" / "14_sota002_high_resolution_supplementary" / "stage16_protocol.json"
HISTORICAL = ROOT / "experiments" / "10_sota_and_scaling" / "SOTA-002" / "historical" / "source_from_monograph.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    require(protocol["protocol_id"] == "STAGE_16_SOTA002_HIGH_RESOLUTION_V1", "Protocol ID mismatch")
    require(protocol["square_resolutions"] == [28, 112, 448, 1024, 2048, 3840], "Square grid mismatch")
    require(protocol["rectangular_resolutions_hw"] == [[1080, 1920], [1440, 2560], [2160, 3840]], "Rectangular grid mismatch")
    require(HISTORICAL.exists(), "Historical SOTA-002 source is missing")
    digest = hashlib.sha256(HISTORICAL.read_bytes()).hexdigest()
    require(digest == protocol["historical_source_sha256"], "Historical SOTA-002 SHA-256 mismatch")

    canonical = ROOT / "inventory" / "experiments.csv"
    if canonical.exists():
        with canonical.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        require(len(rows) == 115, f"Canonical inventory changed: expected 115, got {len(rows)}")

    supplementary = ROOT / "inventory" / "supplementary_experiments.csv"
    require(supplementary.exists(), "Supplementary inventory is missing")
    with supplementary.open("r", encoding="utf-8-sig", newline="") as handle:
        registered = {row["id"]: row for row in csv.DictReader(handle)}
    for unit in protocol["units"]:
        require(unit in registered, f"Supplementary unit is not registered: {unit}")
        require(registered[unit]["relationship_to_pdf"] == "OUTSIDE_115_PDF_CHRONOLOGY", f"Chronology boundary mismatch: {unit}")

    print("STAGE 16 PROTOCOL: PASS | historical_sha256=verified | canonical=115 | supplementary=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
