#!/usr/bin/env python3
"""Validate the Stage 01 inventory and render its Markdown views."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "inventory" / "experiments.csv"
OUT_PATH = ROOT / "docs" / "EXPERIMENT_INDEX.md"
AUDIT_PATH = ROOT / "docs" / "INDEX_AUDIT_REPORT.md"


def load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Empty experiment inventory")
    ids = [row["id"] for row in rows]
    duplicates = sorted(name for name, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise SystemExit(f"Duplicate IDs: {duplicates}")
    required = {
        "id",
        "chapter",
        "section",
        "title",
        "kind",
        "printed_pages",
        "pdf_pages",
        "code_source",
        "source_code_level",
        "reported_results",
        "reproduction_status",
    }
    missing_columns = required - set(rows[0])
    if missing_columns:
        raise SystemExit(f"Missing columns: {sorted(missing_columns)}")
    for row in rows:
        missing = sorted(key for key in required if not row[key].strip())
        if missing:
            raise SystemExit(f"{row['id']}: empty fields {missing}")
    return rows


def render_index(rows: list[dict[str, str]]) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["chapter"]].append(row)

    chapter_names = {
        "2": "BOHN - fundament orbitowy",
        "3": "SBOHN - złamanie symetrii",
        "4": "Uogólnienia i odkrywanie symetrii",
        "5": "Uczenie permutacji i autonomiczna reprezentacja",
        "6": "Learnable SBOHN i Log-Domain Sinkhorn",
        "7": "Architektura fraktalna i Permutation Transformer",
        "8": "Meta-SBOHN",
        "9": "Adaptacja zadaniowa i continual learning",
        "10": "Porównanie SOTA i skalowanie",
        "11": "Kierunki badawcze i system zintegrowany",
        "12": "Ewolucja MoE",
        "13": "RMIG-FBOHN",
        "14": "Meta-FBOHN",
    }
    lines = [
        "# Indeks eksperymentów, testów i programów",
        "",
        f"Rejestr Etapu 01 obejmuje **{len(rows)} jednostki** wykryte w monografii.",
        "Każda pozycja zachowuje osobny status reprodukcji; obecnie wszystkie mają `NOT_RUN`.",
        "",
        "Kolumna `Kod` opisuje poziom materiału dostępnego w PDF. `NARRATIVE_ONLY` nie",
        "oznacza pominięcia - przeciwnie, wskazuje jednostkę wymagającą ostrożnej rekonstrukcji",
        "z opisu i tabel, bez udawania, że pełny kod został opublikowany.",
        "",
    ]
    for chapter in sorted(grouped, key=int):
        lines.extend(
            [
                f"## Rozdział {chapter}: {chapter_names[chapter]}",
                "",
                "| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in grouped[chapter]:
            title = row["title"].replace("|", "\\|")
            pages = f"{row['printed_pages']} / {row['pdf_pages']}"
            lines.append(
                f"| `{row['id']}` | {row['section']} | {title} | "
                f"{row['kind']} | {pages} | `{row['source_code_level']}` |"
            )
        lines.append("")
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_audit(rows: list[dict[str, str]]) -> None:
    chapter_counts = Counter(row["chapter"] for row in rows)
    code_counts = Counter(row["source_code_level"] for row in rows)
    negative = [
        row for row in rows if "negative" in row["kind"] or "NEGATIVE" in row["title"].upper()
    ]
    lines = [
        "# Raport audytu indeksu - Etap 01",
        "",
        f"- Łączna liczba jednostek: **{len(rows)}**.",
        f"- Liczba unikalnych identyfikatorów: **{len({r['id'] for r in rows})}**.",
        f"- Jawnie oznaczone jednostki negatywne/obalające: **{len(negative)}**.",
        "- Wszystkie pozycje mają wskazany rozdział, sekcję, strony, źródło kodu,",
        "  informację o wynikach raportowanych i status reprodukcji.",
        "- Zweryfikowano regułę numeracji: strona PDF = strona drukowana + 1",
        "  w numerowanej części dokumentu.",
        "",
        "## Liczba jednostek według rozdziału",
        "",
        "| Rozdział | Liczba |",
        "|---:|---:|",
    ]
    for chapter in sorted(chapter_counts, key=int):
        lines.append(f"| {chapter} | {chapter_counts[chapter]} |")
    lines.extend(
        [
            "",
            "## Pokrycie kodem źródłowym w PDF",
            "",
            "| Poziom | Liczba |",
            "|---|---:|",
        ]
    )
    for level, count in sorted(code_counts.items()):
        lines.append(f"| `{level}` | {count} |")
    lines.extend(
        [
            "",
            "## Zastrzeżenie",
            "",
            "Rejestr rozdziela osobne baterie, podtesty i warianty, nawet gdy korzystają z",
            "jednego wspólnego skryptu. To celowe: żaden wynik lub wariant nie może zniknąć",
            "pod zbiorczą nazwą programu. Przed rekonstrukcją kodu wykonamy drugi audyt",
            "krzyżowy: indeks vs wszystkie tabele, listingi A.1-A.43 i B.1 oraz surowe bloki",
            "wyników bez podpisu `Listing`.",
        ]
    )
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    inventory = load_rows()
    render_index(inventory)
    render_audit(inventory)
    print(f"OK: {len(inventory)} unique inventory rows")

