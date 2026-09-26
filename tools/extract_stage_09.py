#!/usr/bin/env python3
"""Wyodrębnij Etap 09 w audytowanej kolejności PDF-a."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "07_fractal_patch"

SEQUENCE = [
    {"id": "FR-001", "order": 57, "title": "Fractal Input-Dependent SBOHN — test przełomowy", "caption": "\\caption{Fractal SBOHN results.", "mode": "audit", "level": "CHAPTER_NARRATIVE_TARGET_CODE_ABSENT"},
    {"id": "FR-004", "order": 58, "title": "Fractal SBOHN — analiza per-level modelu InpDep 5L", "caption": "\\caption{Per-level analysis of the InpDep 5L model", "mode": "audit", "level": "CHAPTER_NARRATIVE_TARGET_CODE_ABSENT"},
    {"id": "FR-002", "order": 59, "title": "Fractal SBOHN — MNIST", "caption": "\\caption{Fractal SBOHN on MNIST (digits).", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 13},
    {"id": "FR-003", "order": 60, "title": "Fractal SBOHN — Fashion-MNIST", "caption": "\\caption{Fractal SBOHN on Fashion-MNIST", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 13},
    {"id": "PT-001", "order": 61, "title": "Patch SBOHN / Permutation Transformer — MNIST", "caption": "\\caption{Patch SBOHN --- results on MNIST", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 15},
    {"id": "PT-002", "order": 62, "title": "Patch SBOHN / Permutation Transformer — Fashion-MNIST", "caption": "\\caption{Patch SBOHN --- results on Fashion-MNIST", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 15},
    {"id": "PT-003", "order": 63, "title": "Patch SBOHN — skalowanie względem rozdzielczości", "caption": "\\caption{Scalability of Patch SBOHN", "mode": "audit_context", "level": "SHARED_LISTING_TARGET_CODE_ABSENT", "verbatim": 15},
    {"id": "PT-004", "order": 64, "title": "Patch SBOHN — ablation input-dependency", "caption": "\\caption{Impact of input-dependency", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 15},
    {"id": "PT-005", "order": 65, "title": "Patch SBOHN — ablation liczby głów", "caption": "\\caption{Impact of multi-head", "mode": "run", "level": "FULL_IN_CHAPTER", "verbatim": 15},
    {"id": "HR-001", "order": 66, "title": "HighRes Patch SBOHN — MNIST", "caption": "\\caption{HighRes Patch SBOHN --- results on MNIST", "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-002", "order": 67, "title": "HighRes Patch SBOHN — Fashion-MNIST", "caption": "\\caption{HighRes Patch SBOHN --- results on Fashion-MNIST", "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-003", "order": 68, "title": "HighRes Fractal SBOHN v2 — permutacja patchy kontra cech", "section": ("\\subsection{Key decision: permuting patches vs.\\ features}", "\\subsection{Results}"), "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-004", "order": 69, "title": "HighRes Patch SBOHN — skalowanie do 4K", "caption": "\\caption{Scaling Patch SBOHN to different image resolutions.", "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-005", "order": 70, "title": "HighRes Fractal SBOHN v2 — wkład poprawek", "caption": "\\caption{Evolution of fractal models on MNIST", "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-006", "order": 71, "title": "HighRes Fractal SBOHN v2 — MNIST", "caption": "\\caption{HighRes Fractal SBOHN v2 --- results on MNIST", "mode": "audit", "level": "NARRATIVE_ONLY"},
    {"id": "HR-007", "order": 72, "title": "HighRes Fractal SBOHN v2 — Fashion-MNIST", "caption": "\\caption{HighRes Fractal SBOHN v2 --- results on Fashion-MNIST", "mode": "audit", "level": "NARRATIVE_ONLY"},
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def verbatim_blocks(lines: list[str]) -> list[dict]:
    blocks = []
    index = 0
    while index < len(lines):
        if "\\begin{verbatim}" not in lines[index]:
            index += 1
            continue
        start = index
        index += 1
        content = []
        while index < len(lines) and "\\end{verbatim}" not in lines[index]:
            content.append(lines[index])
            index += 1
        if index == len(lines):
            raise SystemExit("Niezamknięty blok verbatim")
        text = "\n".join(content)
        blocks.append({"start": start + 1, "end": index + 1, "text": text, "sha256": sha(text)})
        index += 1
    return blocks


def audited_verbatim_map() -> dict[int, dict]:
    with (ROOT / "inventory" / "latex_verbatim_map.csv").open(encoding="utf-8", newline="") as stream:
        return {int(row["index"]): row for row in csv.DictReader(stream)}


def table_result(lines: list[str], caption_fragment: str) -> tuple[str, int, int]:
    matches = []
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
        text = "\n".join(lines[start : index + 1])
        if caption_fragment in text:
            matches.append((text, start + 1, index + 1))
        index += 1
    if len(matches) != 1:
        raise SystemExit(f"Oczekiwano jednej tabeli dla: {caption_fragment}; znaleziono {len(matches)}")
    return matches[0]


def section_result(lines: list[str], start_marker: str, end_marker: str) -> tuple[str, int, int]:
    starts = [i for i, line in enumerate(lines) if start_marker in line]
    if len(starts) != 1:
        raise SystemExit(f"Nieunikalny początek sekcji: {start_marker}")
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines)) if end_marker in lines[i]), None)
    if end is None:
        raise SystemExit(f"Brak końca sekcji: {end_marker}")
    return "\n".join(lines[start:end]), start + 1, end


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_09.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = verbatim_blocks(lines)
    audited = audited_verbatim_map()
    if len(blocks) != 20:
        raise SystemExit("Struktura źródła LaTeX zmieniła się")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 09 — Fractal SBOHN i Permutation Transformer\n\n"
        "Pozycje 57–72 zachowują oryginalny porządek PDF-a.\n\n"
        "Pełny kod istnieje dla FR-002/FR-003 oraz PT-001/PT-002/PT-004/PT-005. "
        "Pozostałe jednostki są jawnym audytem wyników źródłowych.\n",
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
        target_code = item["mode"] == "run"
        if "verbatim" in item:
            block = blocks[item["verbatim"] - 1]
            if block["sha256"] != audited[item["verbatim"]]["sha256"]:
                raise SystemExit(f"Niezgodny hash verbatim {item['verbatim']} dla {item['id']}")
            source_name = "source_from_monograph.py" if target_code else "shared_listing_context_from_monograph.py"
            (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
            source_files.append(source_name)
            source_hashes.append(block["sha256"])
            source_ranges.append([block["start"], block["end"]])

        if "caption" in item:
            result_text, result_start, result_end = table_result(lines, item["caption"])
        else:
            result_text, result_start, result_end = section_result(lines, *item["section"])
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
            "verbatim_indices": [item["verbatim"]] if "verbatim" in item else [],
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
            evidence = "Kompletny kod docelowy znajduje się w opublikowanym bloku rozdziału 7."
        elif item["mode"] == "audit_context":
            evidence = "Wspólny kod Patch SBOHN zachowano jako kontekst, ale nie wykonuje on opublikowanego sweepu rozdzielczości."
        else:
            evidence = "Monografia publikuje wynik, lecz nie kompletny kod docelowy tej jednostki."
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 09: **{stage_position}/16**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"{evidence}\n\nTryb: `{execution_mode}`. Wynik źródłowy: wiersze LaTeX {result_start}–{result_end}.\n",
            encoding="utf-8",
        )
        (runner / "run.py").write_text(unit_runner(item["id"]), encoding="utf-8")

    print("EXTRACTION PASS: 16 Stage 09 units in original PDF chronology")
    print("SOURCE BOUNDARY: 6 executable units from 2 shared programs; 10 audited-only units")


if __name__ == "__main__":
    main()
