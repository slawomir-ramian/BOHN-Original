#!/usr/bin/env python3
"""Utwórz metadane pięciu eksperymentów uzupełniających Etapu 07."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "05_permutation_and_representation_supplementary"
UNITS = [
    ("PL-002R", "PL-002", "Uczenie dwóch permutacji"),
    ("PL-003R", "PL-003", "Skalowanie liczby permutacji K"),
    ("HD-003R", "HD-003", "Wariant proportional-signal"),
    ("CMP-001R", "CMP-001", "PCA-48 kontra autoenkoder rekonstrukcyjny"),
    ("CMP-002R", "CMP-002", "Nadzorowany latent k=2,4,8,16"),
]


def runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_07r.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "README.md").write_text(
        "# Etap 07R — jawne rekonstrukcje uzupełniające\n\n"
        "Pięć eksperymentów leży poza chronologią 115 jednostek PDF-a. "
        "Nie są kodem historycznym ani zamiennikiem oryginalnego Etapu 07.\n",
        encoding="utf-8",
    )
    for position, (experiment_id, parent_id, title) in enumerate(UNITS, 1):
        base = BASE / experiment_id
        (base / "runner").mkdir(parents=True, exist_ok=True)
        provenance = {
            "experiment_id": experiment_id,
            "parent_pdf_unit": parent_id,
            "supplementary_sequence": position,
            "relationship_to_pdf": "OUTSIDE_115_PDF_CHRONOLOGY",
            "kind": "parallel_supplementary_reconstruction",
            "historical_source_claimed": False,
            "protocol_id": "STAGE_07R_V1",
            "protocol_status": "FROZEN_BEFORE_CONFIRMATION",
            "reproduction_status": "NOT_RUN",
        }
        (base / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (base / "README_PL.md").write_text(
            f"# {experiment_id} — {title}\n\n"
            f"Eksperyment uzupełniający do `{parent_id}`. Leży poza oryginalną "
            "chronologią 115 jednostek. Kod został jawnie odtworzony z opisu "
            "monografii i nie jest przedstawiany jako kod historyczny.\n\n"
            "Protokół: `../STAGE_07R_PROTOCOL.json`; blokada: "
            "`../STAGE_07R_PROTOCOL_LOCK.json`.\n",
            encoding="utf-8",
        )
        (base / "runner" / "run.py").write_text(runner(experiment_id), encoding="utf-8")
    print("MATERIALIZATION PASS: 5 supplementary Stage 07R units")


if __name__ == "__main__":
    main()
