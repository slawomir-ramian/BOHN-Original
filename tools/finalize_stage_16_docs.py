#!/usr/bin/env python3
"""Idempotently add the validated Stage 16 summary to public documentation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def upsert(path: Path, start: str, end: str, body: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing documentation file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8-sig")
    block = f"{start}\n{body.rstrip()}\n{end}"
    if start in text:
        if end not in text:
            raise RuntimeError(f"Incomplete marker block: {path.relative_to(ROOT)}")
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        updated = before.rstrip() + "\n\n" + block + after
    else:
        updated = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> int:
    upsert(
        ROOT / "README.md",
        "<!-- STAGE_16_SUPPLEMENTARY_START -->",
        "<!-- STAGE_16_SUPPLEMENTARY_END -->",
        """## Etap 16 — uzupełniający benchmark wysokich rozdzielczości

Po zamknięciu kanonicznych 115 jednostek wykonano dwie jawnie uzupełniające
jednostki związane z `SOTA-002`: bezpośrednią replikację wysokorozdzielczą
`SOTA-002R` oraz stałoparametrowy wariant hierarchiczny `SOTA-002H`.

Wynik: `TECHNICAL_CONFIRMATION_WITH_LIMITATIONS`. Historyczny rdzeń zachował
16 tokenów i przy 3840×3840 był 35,67× szybszy od prostego CNN z listingu.
Nowy wariant zachował 51 434 parametry dla wszystkich rozdzielczości, ale nie
wykazał stałego czasu całego pipeline'u ani przewagi jakości klasyfikacji.

Szczegóły: [`docs/STAGE_16_LOCAL_ANALYSIS.md`](docs/STAGE_16_LOCAL_ANALYSIS.md).""",
    )
    english = ROOT / "README_EN.md"
    if english.exists():
        upsert(
            english,
            "<!-- STAGE_16_SUPPLEMENTARY_START -->",
            "<!-- STAGE_16_SUPPLEMENTARY_END -->",
            """## Stage 16 — supplementary high-resolution benchmark

After closing the canonical 115-unit chronology, two explicitly supplementary
units were executed for `SOTA-002`: direct high-resolution replication
`SOTA-002R` and fixed-parameter hierarchical variant `SOTA-002H`.

Result: `TECHNICAL_CONFIRMATION_WITH_LIMITATIONS`. The historical relational
core retained 16 tokens and was 35.67× faster than the listing's simple CNN at
3840×3840. The new variant retained 51,434 parameters at every resolution, but
no constant end-to-end runtime or classification-accuracy advantage is claimed.

Details: [`docs/STAGE_16_LOCAL_ANALYSIS.md`](docs/STAGE_16_LOCAL_ANALYSIS.md).""",
        )
    upsert(
        ROOT / "docs" / "EXPERIMENT_INDEX.md",
        "<!-- STAGE_16_SUPPLEMENTARY_START -->",
        "<!-- STAGE_16_SUPPLEMENTARY_END -->",
        """## Eksperymenty uzupełniające Etapu 16

Te jednostki nie należą do kanonicznych 115 pozycji uporządkowanych według PDF:

- `SOTA-002R` — bezpośrednia replikacja wysokich rozdzielczości;
- `SOTA-002H` — nowy hierarchiczny front-end o stałej liczbie parametrów.

Pełny przebieg: `reproduced/stage_16_runs/20261003T062344Z`.  
Ocena: `TECHNICAL_CONFIRMATION_WITH_LIMITATIONS`.""",
    )
    upsert(
        ROOT / "docs" / "REPOSITORY_STRUCTURE.md",
        "<!-- STAGE_16_SUPPLEMENTARY_START -->",
        "<!-- STAGE_16_SUPPLEMENTARY_END -->",
        """## Rozszerzenie po wydaniu v1.0.0: Etap 16

- `experiments/14_sota002_high_resolution_supplementary/` — protokół i dwie jednostki;
- `src/bohn_original/stage16_high_resolution.py` — nowy wariant H;
- `reproduced/stage_16_runs/` — wyniki i manifesty;
- `docs/STAGE_16_LOCAL_ANALYSIS.md` — kontrolowana interpretacja.""",
    )
    print("STAGE 16 DOCUMENTATION FINALIZATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

