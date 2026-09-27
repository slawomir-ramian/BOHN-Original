#!/usr/bin/env python3
"""Wyodrębnij Etap 11 i zachowaj rzeczywistą granicę opublikowanego kodu."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "09_adaptation_and_continual"

LISTING_HASHES = {
    58: "1b25fe9bcb44d6a822d886f6e3e112bfdf6e48696fab20acc5f7d7d72d1c2edd",
    59: "bfa5c0cd6d989d782a54c943347e3b681ec4a51dc01ae7bc352f385faf7645ea",
}

SEQUENCE = [
    {
        "id": "AD-001", "order": 83,
        "title": "Perm+Head — porównanie sześciu metod adaptacji", "listing": 58,
        "labels": [
            "tab:perm_head_fewshot",
            "tab:param_efficiency",
        ],
    },
    {
        "id": "AD-002", "order": 84,
        "title": "Few-shot transfer MNIST → Fashion-MNIST", "listing": 59,
        "labels": [
            "tab:fewshot_base",
            "tab:fewshot_transfer",
        ],
    },
    {
        "id": "AD-003", "order": 85,
        "title": "Head-only vs full-tune — test modularności enkodera", "listing": 59,
        "labels": ["tab:fewshot_transfer"],
    },
    {
        "id": "CL-001", "order": 86,
        "title": "Continual learning — przełączanie zadań i forgetting", "listing": 58,
        "labels": ["tab:continual_perm_head"],
    },
    {
        "id": "CL-002", "order": 87,
        "title": "Continual learning — wariant perm-only z większym modelem", "listing": 59,
        "labels": ["tab:continual_fewshot"],
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
            raise SystemExit("Niezamknięty blok lstlisting")
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
            raise SystemExit("Niezamknięta tabela")
        tables.append(("\n".join(lines[start:index + 1]), start + 1, index + 1))
        index += 1
    return tables


def reported_tables(tables: list[tuple[str, int, int]], labels: list[str]) -> tuple[str, int, int]:
    selected = []
    for label in labels:
        marker = f"\\label{{{label}}}"
        matches = [table for table in tables if marker in table[0]]
        if len(matches) != 1:
            raise SystemExit(f"Oczekiwano jednej tabeli z etykietą {label}; znaleziono {len(matches)}")
        selected.append(matches[0])
    return "\n\n".join(item[0] for item in selected), selected[0][1], selected[-1][2]


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_11.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    tables = all_tables(lines)
    if len(blocks) != 74:
        raise SystemExit("Struktura źródła LaTeX zmieniła się")
    for index, expected in LISTING_HASHES.items():
        if blocks[index - 1]["sha256"] != expected:
            raise SystemExit(f"Niezgodny hash listingu {index}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 11 — adaptacja zadaniowa i continual learning\n\n"
        "Pozycje 83–87 zachowują kolejność PDF-a. Listingi 58 i 59 publikują "
        "architektury, przygotowanie danych i początek protokołu, ale fazy "
        "adaptacji i continual learning są zastąpione komentarzami. Niezmienione "
        "fragmenty historyczne są oddzielone od jawnej rekonstrukcji.\n",
        encoding="utf-8",
    )

    for position, item in enumerate(SEQUENCE, 1):
        base = OUT / item["id"]
        historical = base / "historical"
        reconstruction = base / "reconstruction"
        historical.mkdir(parents=True, exist_ok=True)
        reconstruction.mkdir(parents=True, exist_ok=True)

        block = blocks[item["listing"] - 1]
        source_name = "source_fragment_from_monograph.py"
        (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
        result_text, result_start, result_end = reported_tables(tables, item["labels"])
        result_text = result_text.rstrip("\n")
        result_name = "reported_result_from_monograph.tex"
        (historical / result_name).write_text(result_text + "\n", encoding="utf-8", newline="\n")

        provenance = {
            "experiment_id": item["id"],
            "source_sequence_in_stage": position,
            "source_order_in_monograph": item["order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": "SOURCE_FRAGMENT_ONLY",
            "execution_mode": "RECONSTRUCTION_FROM_PUBLISHED_FRAGMENT",
            "listing_indices": [item["listing"]],
            "listing_target_code_present": False,
            "historical_source_files": [source_name],
            "historical_source_sha256": [block["sha256"]],
            "historical_source_line_ranges": [[block["start"], block["end"]]],
            "reported_result_file": result_name,
            "reported_result_start_line": result_start,
            "reported_result_end_line": result_end,
            "reported_result_sha256": sha(result_text),
            "historical_code_modified": False,
            "reconstruction_is_historical_source": False,
            "reconstruction_protocol": "STAGE_11_RECONSTRUCTION_V1",
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 11: **{position}/5**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"Listing {item['listing']} jest zachowany bez zmian, lecz pomija kod faz docelowych. "
            "Uruchamiany program jest jawną rekonstrukcją z opublikowanej architektury, "
            "hiperparametrów, opisu i tabel — nie historycznym listingiem wykonawczym.\n",
            encoding="utf-8",
        )
        (reconstruction / "reproduce.py").write_text(unit_runner(item["id"]), encoding="utf-8")

    print("EXTRACTION PASS: 5 Stage 11 units in original PDF chronology")
    print("SOURCE BOUNDARY: listings 58-59 are partial; omitted phases are reconstructed explicitly")


if __name__ == "__main__":
    main()
