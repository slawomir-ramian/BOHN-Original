#!/usr/bin/env python3
"""Wyodrębnij rozdział SBOHN w oryginalnej kolejności źródłowej PDF-a."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "03_sbohn"

# Kolejność jest historyczna (PDF/LaTeX), a nie numeryczna według ID.
SOURCE_SEQUENCE = [
    {"id": "S-001", "listing": 10, "result_listing": 11},
    {"id": "S-002", "listing": 12, "result_listing": 13},
    {"id": "S-003", "listing": 14, "result_listing": 15},
    {"id": "S-004", "listing": 16, "result_listing": 17},
    {"id": "S-005", "listing": 18, "result_listing": 19},
    {"id": "S-006", "listing": 20, "result_listing": 21},
    {"id": "S-010", "listing": 22},
    {"id": "S-011", "listing": 23, "result_verbatim": 8},
    {"id": "S-007", "listing": 24, "result_listing": 25},
    {"id": "S-008", "listing": 26, "result_listing": 27},
    {"id": "S-009", "listing": 28, "result_listing": 29},
]


def extract_blocks(lines: list[str], environment: str) -> list[dict]:
    begin = f"\\begin{{{environment}}}"
    end = f"\\end{{{environment}}}"
    blocks = []
    index = 0
    while index < len(lines):
        if begin not in lines[index]:
            index += 1
            continue
        start = index
        cursor = index + 1
        while cursor < len(lines) and end not in lines[cursor]:
            cursor += 1
        if cursor >= len(lines):
            raise SystemExit(f"Niezamknięty blok {environment}, wiersz {start + 1}")
        content = "\n".join(lines[start + 1 : cursor])
        blocks.append(
            {
                "start_line": start + 1,
                "end_line": cursor + 1,
                "content": content,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )
        index = cursor + 1
    return blocks


def load_hashes(path: Path) -> dict[int, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {int(row["index"]): row["sha256"] for row in csv.DictReader(handle)}


def runner_text(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
"""Uruchom {experiment_id} przez wspólny runner Etapu 04."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_04.py"), "--only", "{experiment_id}"],
    cwd=ROOT,
))
'''


def readme_text(item: dict, position: int, listing: dict, has_result: bool) -> str:
    result_note = (
        "Historyczny wydruk znajduje się w `historical/reported_results.txt`."
        if has_result
        else "Dla tej jednostki źródło nie zawiera osobnego historycznego wydruku."
    )
    return f"""# {item['id']}

Pozycja w chronologii rozdziału SBOHN: **{position}/11**.

Oryginalny kod znajduje się w `historical/source_from_monograph.py` i został
wyodrębniony bez zmian z bloku `lstlisting` nr {item['listing']} (wiersze LaTeX
{listing['start_line']}--{listing['end_line']}). {result_note}

Numer ID nie określa kolejności historycznej. Nadrzędna jest kolejność PDF-a
zapisana w `inventory/source_chronology.csv`.
"""


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    listings = extract_blocks(lines, "lstlisting")
    verbatim = extract_blocks(lines, "verbatim")
    listing_hashes = load_hashes(ROOT / "inventory" / "latex_listing_map.csv")
    verbatim_hashes = load_hashes(ROOT / "inventory" / "latex_verbatim_map.csv")
    if len(listings) != 74 or len(verbatim) != 20:
        raise SystemExit("Struktura źródła zmieniła się; ekstrakcję przerwano.")

    for position, item in enumerate(SOURCE_SEQUENCE, 1):
        experiment_id = item["id"]
        listing_index = item["listing"]
        listing = listings[listing_index - 1]
        if listing["sha256"] != listing_hashes[listing_index]:
            raise SystemExit(f"Niezgodny hash listingu dla {experiment_id}")
        base = OUT / experiment_id
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)
        (historical / "source_from_monograph.py").write_text(
            listing["content"] + "\n", encoding="utf-8", newline="\n"
        )

        result = None
        result_environment = None
        result_index = None
        if "result_listing" in item:
            result_environment = "lstlisting"
            result_index = item["result_listing"]
            result = listings[result_index - 1]
            expected_hash = listing_hashes[result_index]
        elif "result_verbatim" in item:
            result_environment = "verbatim"
            result_index = item["result_verbatim"]
            result = verbatim[result_index - 1]
            expected_hash = verbatim_hashes[result_index]
        if result is not None:
            if result["sha256"] != expected_hash:
                raise SystemExit(f"Niezgodny hash wyniku dla {experiment_id}")
            (historical / "reported_results.txt").write_text(
                result["content"] + "\n", encoding="utf-8", newline="\n"
            )

        provenance = {
            "experiment_id": experiment_id,
            "source_sequence_in_chapter": position,
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "listing_index": listing_index,
            "latex_start_line": listing["start_line"],
            "latex_end_line": listing["end_line"],
            "historical_source_sha256": listing["sha256"],
            "reported_result_environment": result_environment,
            "reported_result_index": result_index,
            "reported_result_sha256": result["sha256"] if result else None,
            "historical_code_modified": False,
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (base / "README_PL.md").write_text(
            readme_text(item, position, listing, result is not None),
            encoding="utf-8",
            newline="\n",
        )
        (runner / "run.py").write_text(
            runner_text(experiment_id), encoding="utf-8", newline="\n"
        )

    print("EXTRACTION PASS: 11 SBOHN units in original PDF chronology")


if __name__ == "__main__":
    main()
