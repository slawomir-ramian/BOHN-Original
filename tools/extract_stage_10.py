#!/usr/bin/env python3
"""Wyodrębnij Etap 10 w audytowanej kolejności PDF-a."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "08_meta_sbohn"

SEQUENCE = [
    {"id": "MS-001", "order": 73, "title": "Meta-SBOHN Score Generator v1", "captions": ["\\caption{Meta-SBOHN Score Generator v1.}"], "level": "NARRATIVE_ONLY"},
    {"id": "MS-002", "order": 74, "title": "Meta-SBOHN v2 — Geometry-Aware Generator", "captions": ["\\caption{Meta-SBOHN v2 with geometric generator.}"], "level": "NARRATIVE_ONLY"},
    {"id": "MS-003", "order": 75, "title": "Meta-SBOHN v2 + SRL", "captions": ["\\caption{Meta-SBOHN v2 + SRL.}"], "level": "NARRATIVE_ONLY"},
    {"id": "MS-004", "order": 76, "title": "Meta-Meta-SBOHN v1", "captions": ["\\caption{Meta-Meta-SBOHN v1 on new tasks.}"], "level": "NARRATIVE_ONLY"},
    {"id": "MS-005", "order": 77, "title": "SBOHN-Curriculum v1 — prosty warm-start", "captions": ["\\caption{Curriculum v1: single \\(\\theta\\) transfer.}"], "level": "SOURCE_FRAGMENT_ONLY", "listing": 57},
    {"id": "MS-006", "order": 78, "title": "SBOHN-Curriculum v2 — Mixed Population Transfer", "captions": ["\\caption{Curriculum v2: mixed population transfer, single seed.}"], "level": "SOURCE_FRAGMENT_ONLY", "listing": 57},
    {"id": "MS-007", "order": 79, "title": "SBOHN-Curriculum v3 — transfer elit", "captions": ["\\caption{Basin analysis: medium+hard, 50 seeds.}"], "level": "SOURCE_FRAGMENT_ONLY", "listing": 57},
    {"id": "MS-008", "order": 80, "title": "SBOHN-Curriculum v4 — analiza basinów", "captions": ["\\caption{Basin analysis: medium+hard, 50 seeds.}"], "level": "SOURCE_FRAGMENT_ONLY", "listing": 57},
    {"id": "MS-009", "order": 81, "title": "Meta-SBOHN v5 — Geometry Regularization", "captions": ["\\caption{Meta-SBOHN v5: fixed geometry regularization, 20 seeds.}"], "level": "FULL_SHARED_LISTING", "listing": 56},
    {"id": "MS-010", "order": 82, "title": "Meta-SBOHN v6 — Geometry Annealing", "captions": ["\\caption{Meta-SBOHN v6: geometry annealing, 20 seeds.}", "\\caption{Meta-SBOHN v6: mean agreement with the true transformation.}"], "level": "FULL_SHARED_LISTING", "listing": 56},
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def listing_blocks(lines: list[str]) -> list[dict]:
    blocks = []
    index = 0
    while index < len(lines):
        if "\\begin{lstlisting}" not in lines[index]:
            index += 1
            continue
        start = index
        index += 1
        content = []
        while index < len(lines) and "\\end{lstlisting}" not in lines[index]:
            content.append(lines[index])
            index += 1
        if index == len(lines):
            raise SystemExit("Niezamknięty blok lstlisting")
        text = "\n".join(content)
        blocks.append({"start": start + 1, "end": index + 1, "text": text, "sha256": sha(text)})
        index += 1
    return blocks


def audited_listing_map() -> dict[int, dict]:
    path = ROOT / "inventory" / "latex_listing_map.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        return {int(row["index"]): row for row in csv.DictReader(stream)}


def all_tables(lines: list[str]) -> list[tuple[str, int, int]]:
    tables = []
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("\\begin{table}"):
            index += 1
            continue
        start = index
        while index < len(lines) and not lines[index].lstrip().startswith("\\end{table}"):
            index += 1
        if index == len(lines):
            raise SystemExit("Niezamknięta tabela")
        tables.append(("\n".join(lines[start : index + 1]), start + 1, index + 1))
        index += 1
    return tables


def reported_tables(tables: list[tuple[str, int, int]], captions: list[str]) -> tuple[str, int, int]:
    selected = []
    for caption in captions:
        matches = [table for table in tables if caption in table[0]]
        if len(matches) != 1:
            raise SystemExit(f"Oczekiwano jednej tabeli dla: {caption}; znaleziono {len(matches)}")
        selected.append(matches[0])
    return "\n\n".join(item[0] for item in selected), selected[0][1], selected[-1][2]


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_10.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    audited = audited_listing_map()
    tables = all_tables(lines)
    if len(blocks) != 74:
        raise SystemExit("Struktura źródła LaTeX zmieniła się")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 10 — Meta-SBOHN\n\n"
        "Pozycje 73–82 zachowują oryginalny porządek PDF-a.\n\n"
        "Pełny kod istnieje dla MS-009/MS-010. MS-005–MS-008 zachowują "
        "wyłącznie fragment inicjalizacji populacji, a MS-001–MS-004 są audytem wyników.\n",
        encoding="utf-8",
    )

    for stage_position, item in enumerate(SEQUENCE, 1):
        base = OUT / item["id"]
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)

        source_files = []
        source_hashes = []
        source_ranges = []
        target_code = item["level"] == "FULL_SHARED_LISTING"
        if "listing" in item:
            block = blocks[item["listing"] - 1]
            if block["sha256"] != audited[item["listing"]]["sha256"]:
                raise SystemExit(f"Niezgodny hash listingu {item['listing']} dla {item['id']}")
            source_name = "source_from_monograph.py" if target_code else "source_fragment_from_monograph.py"
            (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
            source_files.append(source_name)
            source_hashes.append(block["sha256"])
            source_ranges.append([block["start"], block["end"]])

        result_text, result_start, result_end = reported_tables(tables, item["captions"])
        result_text = result_text.rstrip("\n")
        result_name = "reported_result_from_monograph.tex"
        (historical / result_name).write_text(result_text + "\n", encoding="utf-8", newline="\n")

        execution_mode = "HISTORICAL_SOURCE" if target_code else "AUDITED_REPORTED_RESULT"
        provenance = {
            "experiment_id": item["id"],
            "source_sequence_in_stage": stage_position,
            "source_order_in_monograph": item["order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": item["level"],
            "execution_mode": execution_mode,
            "listing_indices": [item["listing"]] if "listing" in item else [],
            "listing_target_code_present": target_code,
            "historical_source_files": source_files,
            "historical_source_sha256": source_hashes,
            "historical_source_line_ranges": source_ranges,
            "reported_result_file": result_name,
            "reported_result_start_line": result_start,
            "reported_result_end_line": result_end,
            "reported_result_sha256": sha(result_text),
            "historical_code_modified": False,
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        if target_code:
            evidence = "Kompletny wspólny program historyczny znajduje się w listingu 56."
        elif item["level"] == "SOURCE_FRAGMENT_ONLY":
            evidence = "Listing 57 zawiera jedynie inicjalizację populacji, bez kompletnego runnera eksperymentu."
        else:
            evidence = "Monografia publikuje wynik i opis, lecz nie kompletny kod docelowy tej jednostki."
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 10: **{stage_position}/10**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"{evidence}\n\nTryb: `{execution_mode}`. Wynik źródłowy: wiersze LaTeX {result_start}–{result_end}.\n",
            encoding="utf-8",
        )
        (runner / "run.py").write_text(unit_runner(item["id"]), encoding="utf-8")

    print("EXTRACTION PASS: 10 Stage 10 units in original PDF chronology")
    print("SOURCE BOUNDARY: 2 executable units from 1 shared program; 4 source-fragment and 4 narrative-only units")


if __name__ == "__main__":
    main()
