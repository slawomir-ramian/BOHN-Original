#!/usr/bin/env python3
"""Deterministycznie wyodrębnij B-001--B-009 ze źródłowego LaTeX-a."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "02_bohn_foundation"
IDS = [f"B-{number:03d}" for number in range(1, 10)]
REPORTED_BLOCK = {
    "B-001": 1,
    "B-004": 2,
    "B-005": 3,
    "B-006": 4,
    "B-007": 5,
    "B-008": 6,
    "B-009": 7,
}


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
"""Uruchom tylko {experiment_id} przez wspólny, udokumentowany adapter."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_03.py"), "--only", "{experiment_id}"],
    cwd=ROOT,
))
'''


def readme_text(experiment_id: str, listing: dict, has_reported: bool) -> str:
    reported = (
        "`historical/reported_results.txt` zachowuje blok wyniku z monografii."
        if has_reported
        else "Monografia nie zawiera oddzielnego bloku `verbatim` dla tej jednostki; "
        "ewentualny wydruk jest częścią samego listingu."
    )
    return f"""# {experiment_id}

Oryginalny kod znajduje się w `historical/source_from_monograph.py` i został
wyodrębniony bez zmian z Listingu A.{int(experiment_id[-3:])} (wiersze LaTeX
{listing['start_line']}--{listing['end_line']}). {reported}

Plik historyczny zachowuje notebookową zależność od wcześniejszych listingów.
`runner/run.py` uruchamia jednostkę przez warstwę techniczną w `src/bohn_original`;
warstwa ta nie jest przedstawiana jako źródło historyczne.
"""


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    listings = extract_blocks(lines, "lstlisting")
    verbatim = extract_blocks(lines, "verbatim")
    listing_hashes = load_hashes(ROOT / "inventory" / "latex_listing_map.csv")
    verbatim_hashes = load_hashes(ROOT / "inventory" / "latex_verbatim_map.csv")
    if len(listings) != 74 or len(verbatim) != 20:
        raise SystemExit("Struktura źródła zmieniła się; ekstrakcję przerwano.")

    for position, experiment_id in enumerate(IDS, 1):
        listing = listings[position - 1]
        if listing["sha256"] != listing_hashes[position]:
            raise SystemExit(f"Niezgodny hash Listingu A.{position}")
        base = OUT / experiment_id
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)
        (historical / "source_from_monograph.py").write_text(
            listing["content"] + "\n", encoding="utf-8", newline="\n"
        )
        reported_index = REPORTED_BLOCK.get(experiment_id)
        reported_hash = None
        if reported_index is not None:
            reported = verbatim[reported_index - 1]
            if reported["sha256"] != verbatim_hashes[reported_index]:
                raise SystemExit(f"Niezgodny hash wyniku {experiment_id}")
            (historical / "reported_results.txt").write_text(
                reported["content"] + "\n", encoding="utf-8", newline="\n"
            )
            reported_hash = reported["sha256"]
        (runner / "run.py").write_text(
            runner_text(experiment_id), encoding="utf-8", newline="\n"
        )
        provenance = {
            "experiment_id": experiment_id,
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "listing_index": position,
            "latex_start_line": listing["start_line"],
            "latex_end_line": listing["end_line"],
            "historical_source_sha256": listing["sha256"],
            "reported_result_sha256": reported_hash,
            "historical_code_modified": False,
            "runner_layer": "technical_adapter",
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (base / "README_PL.md").write_text(
            readme_text(experiment_id, listing, reported_index is not None),
            encoding="utf-8",
            newline="\n",
        )
    print("EXTRACTION PASS: B-001--B-009; listing hashes verified")


if __name__ == "__main__":
    main()
