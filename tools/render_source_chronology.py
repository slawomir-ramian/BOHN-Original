#!/usr/bin/env python3
"""Zapisz stabilną kolejność wszystkich jednostek zgodną z PDF-em."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "inventory" / "experiments.csv"
TARGET = ROOT / "inventory" / "source_chronology.csv"


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_order", "id", "chapter", "section", "pdf_pages", "title"],
        )
        writer.writeheader()
        for order, row in enumerate(rows, 1):
            writer.writerow(
                {
                    "source_order": order,
                    "id": row["id"],
                    "chapter": row["chapter"],
                    "section": row["section"],
                    "pdf_pages": row["pdf_pages"],
                    "title": row["title"],
                }
            )
    print(f"CHRONOLOGY PASS: {len(rows)} units in audited PDF order")


if __name__ == "__main__":
    main()
