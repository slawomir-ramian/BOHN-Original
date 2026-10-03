#!/usr/bin/env python3
"""Register Stage 16 outside the canonical 115-row PDF inventory."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDNAMES = [
    "id", "parent_id", "title", "kind", "relationship_to_pdf",
    "protocol_status", "reproduction_status", "result_path",
]
ROWS = [
    {
        "id": "SOTA-002R",
        "parent_id": "SOTA-002",
        "title": "Direct high-resolution replication of historical SOTA-002",
        "kind": "supplementary replication",
        "relationship_to_pdf": "OUTSIDE_115_PDF_CHRONOLOGY",
        "protocol_status": "PREREGISTERED_BEFORE_EXECUTION",
        "reproduction_status": "NOT_RUN",
        "result_path": "",
    },
    {
        "id": "SOTA-002H",
        "parent_id": "SOTA-002",
        "title": "Hierarchical fixed-parameter high-resolution front-end",
        "kind": "supplementary architectural experiment",
        "relationship_to_pdf": "OUTSIDE_115_PDF_CHRONOLOGY",
        "protocol_status": "PREREGISTERED_BEFORE_EXECUTION",
        "reproduction_status": "NOT_RUN",
        "result_path": "",
    },
]


def register(path: Path) -> tuple[int, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, str]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDNAMES:
                raise RuntimeError(
                    "Unexpected supplementary inventory columns: "
                    + repr(reader.fieldnames)
                )
            existing = list(reader)

    by_id = {row["id"]: row for row in existing}
    added = 0
    for row in ROWS:
        if row["id"] in by_id:
            current = by_id[row["id"]]
            for key in ("parent_id", "kind", "relationship_to_pdf", "protocol_status"):
                if current[key] != row[key]:
                    raise RuntimeError(f"Conflicting {row['id']} field: {key}")
            continue
        existing.append(row)
        by_id[row["id"]] = row
        added += 1

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
    return added, len(existing)


def main() -> int:
    added, total = register(ROOT / "inventory" / "supplementary_experiments.csv")
    print(f"STAGE 16 REGISTRATION: PASS | added={added} | supplementary_total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

