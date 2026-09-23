#!/usr/bin/env python3
"""Wyodrębnij Etap 05 w oryginalnej kolejności PDF-a."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "04_generalization_so2"

SOURCE_SEQUENCE = [
    {"id": "G-001", "source_order": 21, "listing": 30, "result_listing": 31,
     "source_level": "FULL", "execution_mode": "HISTORICAL_SOURCE"},
    {"id": "SO-001", "source_order": 22, "listing": 32, "result_listing": 33,
     "source_level": "FULL_SILENT", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-002", "source_order": 23, "result_listing": 34,
     "source_level": "FORMULA_AND_RESULT", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-003", "source_order": 24, "result_listing": 35,
     "source_level": "FORMULA_AND_RESULT", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-004", "source_order": 25, "result_listing": 36,
     "source_level": "FORMULA_AND_RESULT", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-005", "source_order": 26, "fragment_listing": 37, "result_listing": 38,
     "source_level": "PARTIAL_SHARED", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-006", "source_order": 27, "fragment_listing": 37, "result_listing": 39,
     "source_level": "PARTIAL_SHARED", "execution_mode": "RECONSTRUCTION"},
    {"id": "SO-007", "source_order": 28, "fragment_listing": 37, "result_listing": 40,
     "source_level": "PARTIAL_SHARED", "execution_mode": "RECONSTRUCTION"},
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
        blocks.append({
            "start_line": start + 1,
            "end_line": cursor + 1,
            "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        })
        index = cursor + 1
    return blocks


def load_hashes(path: Path) -> dict[int, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {int(row["index"]): row["sha256"] for row in csv.DictReader(handle)}


def runner_text(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
"""Uruchom {experiment_id} przez wspólny runner Etapu 05."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_05.py"), "--only", "{experiment_id}"],
    cwd=ROOT,
))
'''


def readme_text(item: dict, position: int, source_note: str, result: dict) -> str:
    return f"""# {item['id']}

Pozycja w Etapie 05: **{position}/8**. Pozycja w pełnej chronologii:
**{item['source_order']}/115**.

{source_note}

Historyczny wydruk znajduje się w `historical/reported_results.txt` i pochodzi
z bloku `lstlisting` nr {item['result_listing']} (wiersze LaTeX
{result['start_line']}--{result['end_line']}). Tryb wykonania:
`{item['execution_mode']}`.

Nadrzędna jest kolejność PDF-a zapisana w
`inventory/source_chronology.csv`.
"""


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    listings = extract_blocks(lines, "lstlisting")
    hashes = load_hashes(ROOT / "inventory" / "latex_listing_map.csv")
    if len(listings) != 74:
        raise SystemExit("Struktura źródła zmieniła się; ekstrakcję przerwano.")

    for position, item in enumerate(SOURCE_SEQUENCE, 1):
        experiment_id = item["id"]
        base = OUT / experiment_id
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)

        source_block = None
        source_index = item.get("listing") or item.get("fragment_listing")
        source_filename = None
        if source_index is not None:
            source_block = listings[source_index - 1]
            if source_block["sha256"] != hashes[source_index]:
                raise SystemExit(f"Niezgodny hash kodu dla {experiment_id}")
            source_filename = (
                "source_from_monograph.py" if "listing" in item
                else "source_fragment_from_monograph.py"
            )
            (historical / source_filename).write_text(
                source_block["content"] + "\n", encoding="utf-8", newline="\n"
            )
            source_note = (
                f"Materiał źródłowy znajduje się w `historical/{source_filename}` "
                f"i pochodzi z listingu nr {source_index} (wiersze LaTeX "
                f"{source_block['start_line']}--{source_block['end_line']})."
            )
        else:
            source_note = (
                "Monografia nie zawiera listingu kodu tej jednostki. Rekonstrukcja "
                "w `reconstruction/reproduce.py` wynika z opublikowanego wzoru."
            )

        result_index = item["result_listing"]
        result = listings[result_index - 1]
        if result["sha256"] != hashes[result_index]:
            raise SystemExit(f"Niezgodny hash wyniku dla {experiment_id}")
        (historical / "reported_results.txt").write_text(
            result["content"] + "\n", encoding="utf-8", newline="\n"
        )

        provenance = {
            "experiment_id": experiment_id,
            "source_sequence_in_stage": position,
            "source_order_in_monograph": item["source_order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": item["source_level"],
            "execution_mode": item["execution_mode"],
            "listing_index": source_index,
            "source_filename": source_filename,
            "latex_start_line": source_block["start_line"] if source_block else None,
            "latex_end_line": source_block["end_line"] if source_block else None,
            "historical_source_sha256": source_block["sha256"] if source_block else None,
            "reported_result_index": result_index,
            "reported_result_sha256": result["sha256"],
            "historical_code_modified": False,
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        (base / "README_PL.md").write_text(
            readme_text(item, position, source_note, result),
            encoding="utf-8", newline="\n",
        )
        (runner / "run.py").write_text(
            runner_text(experiment_id), encoding="utf-8", newline="\n"
        )

    print("EXTRACTION PASS: 8 Stage 05 units in original PDF chronology")


if __name__ == "__main__":
    main()
