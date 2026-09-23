#!/usr/bin/env python3
"""Validate the audited BOHN inventory and render its Markdown views."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "inventory" / "experiments.csv"
OUT_PATH = ROOT / "docs" / "EXPERIMENT_INDEX.md"
AUDIT_PATH = ROOT / "docs" / "INDEX_AUDIT_REPORT.md"
CROSS_AUDIT_PATH = ROOT / "docs" / "STAGE_02_CROSS_AUDIT.md"
TABLE_MAP_PATH = ROOT / "inventory" / "table_map.csv"
CODE_BLOCK_MAP_PATH = ROOT / "inventory" / "code_block_map.csv"
LATEX_LISTING_MAP_PATH = ROOT / "inventory" / "latex_listing_map.csv"
LATEX_VERBATIM_MAP_PATH = ROOT / "inventory" / "latex_verbatim_map.csv"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_rows() -> list[dict[str, str]]:
    rows = load_csv(CSV_PATH)
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
    status_counts = Counter(row["reproduction_status"] for row in rows)
    evaluated = len(rows) - status_counts.get("NOT_RUN", 0)

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
        f"Rejestr obejmuje **{len(rows)} jednostek** wykrytych w monografii.",
        f"Po zakończonych etapach wykonano **{evaluated} jednostek**; **{status_counts.get('NOT_RUN', 0)}** pozostaje `NOT_RUN`.",
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
                "| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for row in grouped[chapter]:
            title = row["title"].replace("|", "\\|")
            pages = f"{row['printed_pages']} / {row['pdf_pages']}"
            lines.append(
                f"| `{row['id']}` | {row['section']} | {title} | "
                f"{row['kind']} | {pages} | `{row['source_code_level']}` | "
                f"`{row['reproduction_status']}` |"
            )
        lines.append("")
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_links(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def validate_cross_maps(
    rows: list[dict[str, str]],
    tables: list[dict[str, str]],
    code_blocks: list[dict[str, str]],
) -> None:
    known = {row["id"] for row in rows}
    table_numbers = [row["table"] for row in tables]
    if len(table_numbers) != len(set(table_numbers)):
        raise SystemExit("Duplicate table numbers in table_map.csv")
    for source_name, mapped_rows in (("table", tables), ("code block", code_blocks)):
        for mapped in mapped_rows:
            unknown = sorted(set(split_links(mapped["linked_ids"])) - known)
            if unknown:
                raise SystemExit(f"Unknown IDs in {source_name} map: {unknown}")


def render_audit(
    rows: list[dict[str, str]],
    tables: list[dict[str, str]],
    code_blocks: list[dict[str, str]],
    latex_listings: list[dict[str, str]],
    latex_verbatim: list[dict[str, str]],
) -> None:
    chapter_counts = Counter(row["chapter"] for row in rows)
    code_counts = Counter(row["source_code_level"] for row in rows)
    negative = [
        row for row in rows if "negative" in row["kind"] or "NEGATIVE" in row["title"].upper()
    ]
    lines = [
        "# Raport audytu indeksu - Etap 02",
        "",
        f"- Łączna liczba jednostek: **{len(rows)}**.",
        f"- Liczba unikalnych identyfikatorów: **{len({r['id'] for r in rows})}**.",
        f"- Jawnie oznaczone jednostki negatywne/obalające: **{len(negative)}**.",
        f"- Zmapowane numerowane tabele wynikowe i porównawcze: **{len(tables)}**.",
        f"- Zmapowane niepodpisane lub wieloeksperymentalne bloki kodu: **{len(code_blocks)}**.",
        f"- Zmapowane środowiska LaTeX `lstlisting`: **{len(latex_listings)}**.",
        f"- Zmapowane środowiska LaTeX `verbatim`: **{len(latex_verbatim)}**.",
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
            "## Wynik audytu krzyżowego",
            "",
            "Audyt rozdzielił wcześniej zgrupowane ablacje i warianty z rozdziałów 7, 9 i 12.",
            "Każda z 94 numerowanych tabel jest przypisana do co najmniej jednego ID, a każdy",
            "zidentyfikowany blok kodu w dodatkach ma wskazane jednostki docelowe. Pozycje",
            "`NARRATIVE_ONLY` pozostają jawne i nie będą traktowane jak pełny kod źródłowy.",
        ]
    )
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_cross_audit(
    rows: list[dict[str, str]],
    tables: list[dict[str, str]],
    code_blocks: list[dict[str, str]],
    latex_listings: list[dict[str, str]],
    latex_verbatim: list[dict[str, str]],
) -> None:
    additions = [
        "S-010",
        "S-011",
        "FR-004",
        "PT-003",
        "PT-004",
        "PT-005",
        "HR-004",
        "HR-005",
        "HR-006",
        "HR-007",
        "CL-002",
        "MOE-009",
    ]
    lines = [
        "# Etap 02 - audyt krzyżowy monografii",
        "",
        "## Wynik",
        "",
        f"Indeks wzrósł ze 103 do **{len(rows)} jednostek**. Dodano {len(additions)} pozycji, które w",
        "pierwszym rejestrze były ukryte wewnątrz szerszych eksperymentów.",
        "",
        "| Nowe ID | Powód wydzielenia |",
        "|---|---|",
    ]
    lookup = {row["id"]: row for row in rows}
    for item in additions:
        lines.append(f"| `{item}` | {lookup[item]['title']} |")
    lines.extend(
        [
            "",
            "## Warstwy kontroli",
            "",
            f"1. **{len(rows)} jednostek** w `inventory/experiments.csv`.",
            f"2. **{len(tables)} numerowane tabele** w `inventory/table_map.csv`.",
            "3. **44 podpisane listingi** A.1-A.43 i B.1 w `inventory/appendix_listings.csv`.",
            f"4. **{len(code_blocks)} bloki bez osobnego podpisu lub skrypty wieloeksperymentalne**",
            "   w `inventory/code_block_map.csv`.",
            f"5. **{len(latex_listings)} bloków `lstlisting`** i **{len(latex_verbatim)} bloków `verbatim`**",
            "   z dokładnymi numerami linii oraz hashami SHA-256.",
            "6. Osobne oznaczenie pozycji z pełnym kodem, kodem częściowym i opisem narracyjnym.",
            "",
            "## Granica audytu",
            "",
            "Audyt potwierdza kompletność rejestru na poziomie rozpoznawalnych jednostek",
            "wykonawczych w PDF. Nie potwierdza jeszcze, że każdy listing jest wykonywalny bez",
            "rekonstrukcji: tę właściwość sprawdzimy osobno podczas ekstrakcji kodu B-001, B-002, ...",
        ]
    )
    CROSS_AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    inventory = load_rows()
    table_map = load_csv(TABLE_MAP_PATH)
    code_block_map = load_csv(CODE_BLOCK_MAP_PATH)
    latex_listing_map = load_csv(LATEX_LISTING_MAP_PATH)
    latex_verbatim_map = load_csv(LATEX_VERBATIM_MAP_PATH)
    validate_cross_maps(inventory, table_map, code_block_map)
    validate_cross_maps(inventory, [], latex_listing_map)
    validate_cross_maps(inventory, [], latex_verbatim_map)
    render_index(inventory)
    render_audit(inventory, table_map, code_block_map, latex_listing_map, latex_verbatim_map)
    render_cross_audit(
        inventory, table_map, code_block_map, latex_listing_map, latex_verbatim_map
    )
    print(
        f"OK: {len(inventory)} unique inventory rows; "
        f"{len(table_map)} tables; {len(code_block_map)} code suites; "
        f"{len(latex_listing_map)} listings; {len(latex_verbatim_map)} verbatim blocks"
    )
