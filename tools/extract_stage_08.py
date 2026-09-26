#!/usr/bin/env python3
"""Wyodrębnij Etap 08 w oryginalnej kolejności PDF-a."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "06_learnable_sinkhorn"

SEQUENCE = [
    {"id": "LS-001", "order": 46, "title": "Learnable SBOHN — pięciokrokowy pipeline Task A i Task B", "listing": 53, "result": (3407, 3436), "target_code": True},
    {"id": "LS-002", "order": 47, "title": "SBOHN-K3 — regularyzacja ortogonalności", "listing": 53, "result": (3442, 3461), "target_code": False},
    {"id": "LS-003", "order": 48, "title": "Input-Dependent SBOHN — annealing i eksplozja NaN", "listing": 53, "result": (3463, 3482), "target_code": False},
    {"id": "LS-004", "order": 49, "title": "Low-Rank Sinkhorn 784x784 — sweep rangu", "listing": 53, "result": (3484, 3504), "target_code": False},
    {"id": "LS-005", "order": 50, "title": "Analiza algebraiczna wyuczonych macierzy", "listing": 53, "result": (3506, 3530), "target_code": False},
    {"id": "LS-006", "order": 51, "title": "Task C — regresja z czterema ukrytymi symetriami", "listing": 53, "result": (3532, 3553), "target_code": False},
    {"id": "LD-001", "order": 52, "title": "Log-domain kontra naive Sinkhorn", "listing": 54, "result": (3587, 3609), "target_code": True},
    {"id": "LD-002", "order": 53, "title": "Input-Dependent log-domain z annealingiem", "listing": 54, "result": (3613, 3636), "target_code": True},
    {"id": "LD-003", "order": 54, "title": "Regularyzacja entropii — Global K=3", "listing": 54, "result": (3640, 3667), "target_code": True},
    {"id": "LD-004", "order": 55, "title": "Full Stack — InpDep K=2 + LogDomain + Entropy + Ortho", "listing": 55, "result": (3671, 3688), "target_code": True},
    {"id": "LD-005", "order": 56, "title": "Analiza algebraiczna modelu regularyzowanego", "listing": 55, "result": (3692, 3730), "target_code": True},
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


def listing_map() -> dict[int, dict]:
    with (ROOT / "inventory" / "latex_listing_map.csv").open(encoding="utf-8", newline="") as stream:
        return {int(row["index"]): row for row in csv.DictReader(stream)}


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_08.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    audited = listing_map()
    if len(blocks) != 74:
        raise SystemExit("Struktura zrodla LaTeX zmienila sie")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 08 — Learnable SBOHN i Log-Domain Sinkhorn\n\n"
        "Jednostki `LS-001`--`LD-005` zachowują pozycje 46--56 PDF-a.\n\n"
        "Listing 53 wykonuje LS-001. Tabele LS-002--LS-006 opisują dalsze eksperymenty, "
        "których kodu wykonawczego listing 53 nie zawiera.\n",
        encoding="utf-8",
    )

    for stage_position, item in enumerate(SEQUENCE, 1):
        base = OUT / item["id"]
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)
        block = blocks[item["listing"] - 1]
        if block["sha256"] != audited[item["listing"]]["sha256"]:
            raise SystemExit(f"Niezgodny hash listingu {item['listing']} dla {item['id']}")
        source_name = "source_from_monograph.py" if item["target_code"] else "shared_listing_context_from_monograph.py"
        (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
        start, end = item["result"]
        result_text = "\n".join(lines[start - 1 : end])
        result_name = "reported_results_from_monograph.tex"
        (historical / result_name).write_text(result_text + "\n", encoding="utf-8", newline="\n")

        execution_mode = "HISTORICAL_SOURCE" if item["target_code"] else "AUDITED_REPORTED_RESULT"
        source_level = "FULL_SHARED_LISTING" if item["target_code"] else "SHARED_LISTING_TARGET_CODE_ABSENT"
        provenance = {
            "experiment_id": item["id"],
            "source_sequence_in_stage": stage_position,
            "source_order_in_monograph": item["order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": source_level,
            "execution_mode": execution_mode,
            "listing_indices": [item["listing"]],
            "listing_target_code_present": item["target_code"],
            "historical_source_files": [source_name],
            "historical_source_sha256": [block["sha256"]],
            "historical_source_line_ranges": [[block["start"], block["end"]]],
            "reported_result_file": result_name,
            "reported_result_start_line": start,
            "reported_result_end_line": end,
            "reported_result_sha256": sha(result_text),
            "historical_code_modified": False,
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if item["target_code"]:
            evidence = f"Kod docelowy znajduje się w opublikowanym listingu {item['listing']}; tryb `HISTORICAL_SOURCE`."
        else:
            evidence = (
                f"Listing {item['listing']} jest przypisany do rozdziału, lecz nie zawiera kodu tego eksperymentu. "
                "Jednostkę kontrolujemy jako `AUDITED_REPORTED_RESULT`; kontekst listingu zachowano bez zmian."
            )
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 08: **{stage_position}/11**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"{evidence}\n\nWyniki źródłowe: wiersze LaTeX {start}--{end}.\n",
            encoding="utf-8",
        )
        (runner / "run.py").write_text(unit_runner(item["id"]), encoding="utf-8")

    print("EXTRACTION PASS: 11 Stage 08 units in original PDF chronology")
    print("SOURCE BOUNDARY: LS-002--LS-006 target code absent from shared listing 53")


if __name__ == "__main__":
    main()
