#!/usr/bin/env python3
"""Wyodrębnij Etap 07 w oryginalnej kolejności PDF-a."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "05_permutation_and_representation"

SEQUENCE = [
    {"id": "PL-001", "order": 34, "title": "SBOHN-PL — uczenie jednej permutacji", "listings": [46], "result": (2177, 2276)},
    {"id": "PL-002", "order": 35, "title": "SBOHN-PL2 — uczenie dwóch permutacji", "listings": [], "result": (2360, 2381)},
    {"id": "PL-003", "order": 36, "title": "SBOHN-K — skalowanie liczby permutacji", "listings": [], "result": (2401, 2417)},
    {"id": "AR-001", "order": 37, "title": "SBOHN-AR v1 — generowanie transformacji", "listings": [47], "result": (2497, 2533)},
    {"id": "AR-002", "order": 38, "title": "SBOHN-AR v2 — Generate–Represent–Select", "listings": [48], "result": (2569, 2614)},
    {"id": "AR-003", "order": 39, "title": "Test korelacji reprezentacji", "listings": [49], "result": (2680, 2701)},
    {"id": "AR-004", "order": 40, "title": "Reprezentacyjne klasy równoważności", "listings": [50], "result": (2776, 2810)},
    {"id": "HD-001", "order": 41, "title": "Skalowanie względem wymiaru", "listings": [51, 52], "result": (2957, 2975)},
    {"id": "HD-002", "order": 42, "title": "Wpływ liczby próbek przy d=4095", "listings": [51, 52], "result": (2993, 3010)},
    {"id": "HD-003", "order": 43, "title": "Wariant proportional-signal", "listings": [], "result": (3043, 3060)},
    {"id": "CMP-001", "order": 44, "title": "PCA-48 kontra autoenkoder", "listings": [], "result": (3080, 3111)},
    {"id": "CMP-002", "order": 45, "title": "Supervised Representation Learning", "listings": [], "result": (3113, 3162)},
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def listing_blocks(lines: list[str]) -> list[dict]:
    output = []
    i = 0
    while i < len(lines):
        if "\\begin{lstlisting}" not in lines[i]:
            i += 1
            continue
        start = i
        i += 1
        content = []
        while i < len(lines) and "\\end{lstlisting}" not in lines[i]:
            content.append(lines[i])
            i += 1
        if i == len(lines):
            raise SystemExit("Niezamknięty blok lstlisting")
        text = "\n".join(content)
        output.append({"start": start + 1, "end": i + 1, "text": text, "sha256": sha(text)})
        i += 1
    return output


def listing_map() -> dict[int, dict]:
    with (ROOT / "inventory" / "latex_listing_map.csv").open(encoding="utf-8", newline="") as stream:
        return {int(row["index"]): row for row in csv.DictReader(stream)}


def unit_runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_07.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    audited = listing_map()
    if len(blocks) != 74:
        raise SystemExit("Struktura źródła LaTeX zmieniła się")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 07 — uczenie permutacji i autonomiczna reprezentacja\n\n"
        "Jednostki `PL-001`--`CMP-002` zachowują pozycje 34--45 PDF-a.\n",
        encoding="utf-8",
    )

    for stage_position, item in enumerate(SEQUENCE, 1):
        base = OUT / item["id"]
        historical = base / "historical"
        runner = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        runner.mkdir(parents=True, exist_ok=True)

        result_start, result_end = item["result"]
        result_text = "\n".join(lines[result_start - 1 : result_end])
        (historical / "reported_results_from_monograph.tex").write_text(
            result_text + "\n", encoding="utf-8", newline="\n"
        )

        source_files = []
        source_hashes = []
        source_ranges = []
        for number, listing_index in enumerate(item["listings"], 1):
            block = blocks[listing_index - 1]
            if block["sha256"] != audited[listing_index]["sha256"]:
                raise SystemExit(f"Niezgodny hash listingu {listing_index} dla {item['id']}")
            filename = "source_from_monograph.py" if len(item["listings"]) == 1 else f"source_fragment_{number}_from_monograph.py"
            (historical / filename).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
            source_files.append(filename)
            source_hashes.append(block["sha256"])
            source_ranges.append([block["start"], block["end"]])

        full_source = bool(item["listings"])
        provenance = {
            "experiment_id": item["id"],
            "source_sequence_in_stage": stage_position,
            "source_order_in_monograph": item["order"],
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": "FULL_UNCAPTIONED" if full_source else "NARRATIVE_ONLY",
            "execution_mode": "HISTORICAL_SOURCE" if full_source else "AUDITED_REPORTED_RESULT",
            "listing_indices": item["listings"],
            "historical_source_files": source_files,
            "historical_source_sha256": source_hashes,
            "historical_source_line_ranges": source_ranges,
            "reported_result_file": "reported_results_from_monograph.tex",
            "reported_result_start_line": result_start,
            "reported_result_end_line": result_end,
            "reported_result_sha256": sha(result_text),
            "historical_code_modified": False,
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        if full_source:
            evidence = f"Pełny kod historyczny: listingi {item['listings']}; wykonanie `HISTORICAL_SOURCE`."
        else:
            evidence = (
                "Monografia nie publikuje pełnego programu. Jednostka jest zachowana jako "
                "`NARRATIVE_ONLY` i kontrolowana jako `AUDITED_REPORTED_RESULT`; nie jest to rekonstrukcja."
            )
        (base / "README_PL.md").write_text(
            f"# {item['id']} — {item['title']}\n\n"
            f"Pozycja Etapu 07: **{stage_position}/12**; chronologia monografii: **{item['order']}/115**.\n\n"
            f"{evidence}\n\n"
            f"Wyniki źródłowe: wiersze LaTeX {result_start}--{result_end}.\n",
            encoding="utf-8",
        )
        (runner / "run.py").write_text(unit_runner(item["id"]), encoding="utf-8")

    print("EXTRACTION PASS: 12 Stage 07 units in original PDF chronology")


if __name__ == "__main__":
    main()
