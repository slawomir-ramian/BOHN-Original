#!/usr/bin/env python3
"""Wyodrębnij pełne listingi i tabele Etapu 12 w kolejności PDF-a."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "10_sota_and_scaling"
LISTING_HASHES = {
    60: "ddc6005c6b4b1b19225dc2c0f47a0eb92f94d0f9e7468b817f4586e499a37942",
    61: "5bbb31513c6983dead35704874fc81b31dd8e5eb1bbc1314061ef7fec645b249",
}
SEQUENCE = [
    {
        "id": "SOTA-001", "order": 88, "listing": 60,
        "title": "Porównanie jakości, parametrów, pamięci i czasu treningu",
        "labels": ["tab:sota_acc"],
    },
    {
        "id": "SOTA-002", "order": 89, "listing": 61,
        "title": "Skalowanie inferencji wraz z rozdzielczością",
        "labels": ["tab:sota_inference", "tab:sota_scaling", "tab:sota_params", "tab:sota_mem"],
    },
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
            raise SystemExit("Niezamkniety blok lstlisting")
        text = "\n".join(content)
        blocks.append({"start": start + 1, "end": index + 1, "text": text, "sha256": sha(text)})
        index += 1
    return blocks


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
            raise SystemExit("Niezamknieta tabela")
        tables.append(("\n".join(lines[start:index + 1]), start + 1, index + 1))
        index += 1
    return tables


def reported_tables(tables, labels):
    selected = []
    for label in labels:
        marker = f"\\label{{{label}}}"
        matches = [table for table in tables if marker in table[0]]
        if len(matches) != 1:
            raise SystemExit(f"Oczekiwano jednej tabeli z etykieta {label}; znaleziono {len(matches)}")
        selected.append(matches[0])
    return "\n\n".join(item[0] for item in selected), selected[0][1], selected[-1][2]


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_12.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    tables = all_tables(lines)
    if len(blocks) != 74:
        raise SystemExit("Struktura zrodla LaTeX zmienila sie")
    for number, expected in LISTING_HASHES.items():
        if blocks[number - 1]["sha256"] != expected:
            raise SystemExit(f"Niezgodny hash listingu {number}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 12 — SOTA i skalowanie\n\n"
        "Pozycje 88–89 zachowują kolejność PDF-a. Pełne listingi 60 i 61 są "
        "archiwizowane bez zmian; uruchomienie stosuje osobną warstwę zgodności "
        "wyłącznie do bezpiecznego przekierowania ścieżek `/tmp`.\n",
        encoding="utf-8",
    )
    for position, item in enumerate(SEQUENCE, 1):
        base = OUT / item["id"]
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)
        block = blocks[item["listing"] - 1]
        source_name = "source_from_monograph.py"
        (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
        result_text, result_start, result_end = reported_tables(tables, item["labels"])
        result_name = "reported_result_from_monograph.tex"
        (historical / result_name).write_text(result_text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        provenance = {
            "experiment_id": item["id"],
            "source_sequence_in_stage": position,
            "source_order_in_monograph": item["order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": "FULL_SOURCE",
            "execution_mode": "HISTORICAL_SOURCE_WITH_PATH_COMPATIBILITY",
            "listing_indices": [item["listing"]],
            "historical_source_files": [source_name],
            "historical_source_sha256": [block["sha256"]],
            "historical_source_line_ranges": [[block["start"], block["end"]]],
            "reported_result_file": result_name,
            "reported_result_start_line": result_start,
            "reported_result_end_line": result_end,
            "reported_result_sha256": sha(result_text.rstrip("\n")),
            "historical_code_modified": False,
            "compatibility_changes": ["redirect_absolute_tmp_paths_in_runtime_copy_only"],
            "hardware_dependent_metrics": ["train_s"] if item["id"] == "SOTA-001" else ["times", "scaling_exp", "est_4k_ms"],
        }
        (base / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 12: **{position}/2**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"Pełny listing {item['listing']} zachowano bez zmian. Warstwa wykonawcza przekierowuje "
            "jedynie ścieżki `/tmp` w kopii roboczej. Czasy są zależne od sprzętu; zgodność "
            "architektury i wniosek naukowy raportowane są oddzielnie.\n",
            encoding="utf-8",
        )
        (runner / "run.py").write_text(unit_runner(item["id"]), encoding="utf-8")
    print("EXTRACTION PASS: 2 Stage 12 units in original PDF chronology")
    print("SOURCE BOUNDARY: full listings 60-61; runtime path compatibility is separate")


if __name__ == "__main__":
    main()
