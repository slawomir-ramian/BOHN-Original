#!/usr/bin/env python3
"""Audit the English LaTeX source and map every code/text block to inventory IDs."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
LISTING_OUT = ROOT / "inventory" / "latex_listing_map.csv"
VERBATIM_OUT = ROOT / "inventory" / "latex_verbatim_map.csv"
REPORT_OUT = ROOT / "docs" / "LATEX_SOURCE_AUDIT.md"
ASSET_OUT = ROOT / "inventory" / "latex_asset_map.csv"


LISTING_LINKS = [
    "B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008", "B-009",
    "S-001", "S-001", "S-002", "S-002", "S-003", "S-003", "S-004", "S-004", "S-005",
    "S-005", "S-006", "S-006", "S-010", "S-011", "S-007", "S-007", "S-008", "S-008",
    "S-009", "S-009", "G-001", "G-001", "SO-001", "SO-001", "SO-002", "SO-003", "SO-004",
    "SO-005;SO-006;SO-007", "SO-005", "SO-006", "SO-007", "SD-001", "SD-002", "SD-003",
    "SD-004", "ASD-001", "PL-001", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001;HD-002",
    "HD-001;HD-002", "LS-001;LS-002;LS-003;LS-004;LS-005;LS-006", "LD-001;LD-002;LD-003",
    "LD-004;LD-005", "MS-009;MS-010", "MS-005;MS-006;MS-007;MS-008", "AD-001",
    "AD-002;AD-003;CL-001;CL-002", "SOTA-001", "SOTA-002", "SYS-001;SYS-002", "SYS-005",
    "SYS-003;SYS-004;CPU-001;CPU-002;CPU-003;CPU-004;CPU-005", "MOE-001;MOE-009",
    "MOE-002;MOE-003", "MOE-004", "MOE-005;MOE-006;MOE-007", "MOE-008",
    "RF-001;RF-002;MF-001;MF-002;MF-003;MF-004;MF-005",
    "RF-001;RF-002;MF-001;MF-002;MF-003;MF-004;MF-005", "RF-001", "RF-002", "MF-005",
]

VERBATIM_LINKS = [
    "B-001", "B-004", "B-005", "B-006", "B-007", "B-008", "B-009", "S-011",
    "SD-001", "SD-002", "SD-003", "SD-004", "FR-002;FR-003", "FR-002;FR-003",
    "PT-001;PT-002;PT-003;PT-004;PT-005", "AD-001", "CL-001;CL-002", "SYS-005",
    "MOE-001;MOE-009", "MOE-008",
]


def extract_blocks(lines: list[str], environment: str) -> list[dict[str, str | int]]:
    begin = f"\\begin{{{environment}}}"
    end = f"\\end{{{environment}}}"
    blocks: list[dict[str, str | int]] = []
    i = 0
    while i < len(lines):
        if begin not in lines[i]:
            i += 1
            continue
        start = i
        j = i + 1
        while j < len(lines) and end not in lines[j]:
            j += 1
        if j >= len(lines):
            raise SystemExit(f"Unclosed {environment} block at line {start + 1}")
        header = lines[start].strip()
        content = "\n".join(lines[start + 1 : j])
        blocks.append(
            {
                "start_line": start + 1,
                "end_line": j + 1,
                "header": header,
                "content": content,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )
        i = j + 1
    return blocks


def listing_kind(header: str) -> str:
    if "language=bash" in header:
        return "usage"
    if "style=textstyle" in header or "basicstyle=" in header:
        return "reported_result"
    return "python_code"


def caption_from_header(header: str) -> str:
    match = re.search(r"caption=\{([^}]*)\}", header)
    if match:
        return match.group(1)
    match = re.search(r"caption=([^,\]]+)", header)
    return match.group(1).strip() if match else ""


def write_map(path: Path, blocks: list[dict[str, str | int]], links: list[str], env: str) -> None:
    if len(blocks) != len(links):
        raise SystemExit(f"{env}: expected {len(links)} blocks, found {len(blocks)}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "index", "environment", "start_line", "end_line", "kind",
            "linked_ids", "caption", "sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for number, (block, linked) in enumerate(zip(blocks, links, strict=True), 1):
            header = str(block["header"])
            kind = listing_kind(header) if env == "lstlisting" else "verbatim_block"
            writer.writerow(
                {
                    "index": number,
                    "environment": env,
                    "start_line": block["start_line"],
                    "end_line": block["end_line"],
                    "kind": kind,
                    "linked_ids": linked,
                    "caption": caption_from_header(header) if env == "lstlisting" else "",
                    "sha256": block["sha256"],
                }
            )


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    chapters = len(re.findall(r"^\\chapter\{", text, flags=re.MULTILINE))
    tables = len(re.findall(r"\\begin\{table\}", text))
    listings = extract_blocks(lines, "lstlisting")
    verbatim = extract_blocks(lines, "verbatim")
    expected = (17, 94, 74, 20)
    actual = (chapters, tables, len(listings), len(verbatim))
    if actual != expected:
        raise SystemExit(f"LaTeX structure mismatch: expected {expected}, found {actual}")

    write_map(LISTING_OUT, listings, LISTING_LINKS, "lstlisting")
    write_map(VERBATIM_OUT, verbatim, VERBATIM_LINKS, "verbatim")

    assets = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text)
    asset_rows = []
    for asset in assets:
        source_line = next(
            number for number, line in enumerate(lines, 1) if f"{{{asset}}}" in line
        )
        candidate = SOURCE.parent / asset
        asset_rows.append(
            {
                "asset": asset,
                "source_line": source_line,
                "present": "YES" if candidate.exists() else "NO",
                "status": "AVAILABLE" if candidate.exists() else "MISSING_RECOVERABLE_FROM_PDF",
            }
        )
    with ASSET_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["asset", "source_line", "present", "status"]
        )
        writer.writeheader()
        writer.writerows(asset_rows)
    missing_assets = [row for row in asset_rows if row["present"] == "NO"]

    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    lines_out = [
        "# Audyt źródłowego LaTeX-a",
        "",
        f"- SHA-256: `{source_hash}`",
        f"- Rozdziały i dodatki: **{chapters}**.",
        f"- Numerowane środowiska tabel: **{tables}**.",
        f"- Bloki `lstlisting`: **{len(listings)}**.",
        f"- Bloki `verbatim`: **{len(verbatim)}**.",
        f"- Referencje do zewnętrznych grafik: **{len(asset_rows)}**.",
        f"- Brakujące grafiki: **{len(missing_assets)}**.",
        "",
        "## Wnioski dla indeksu",
        "",
        "1. Źródło potwierdza dokładnie 94 numerowane tabele obecne w polskim PDF.",
        "2. Ujawniło dwa osobne elementy SBOHN-LR: kod referencyjny (`S-010`) oraz",
        "   benchmark 100 seedów (`S-011`).",
        "3. Potwierdza, że pełny kod Meta-SBOHN v1, v2, v2+SRL i Meta-Meta-SBOHN v1",
        "   nie występuje w dodatku A.6; pozycje te pozostają `NARRATIVE_ONLY`.",
        "4. Każdy blok źródłowy ma osobny hash SHA-256 i powiązanie z ID eksperymentu.",
        "5. Dwa pełne skrypty Fractal/Patch znajdują się w blokach `verbatim` w tekście",
        "   głównym, a nie w dodatku. Nie wolno ich pominąć podczas ekstrakcji kodu.",
        "6. Źródło nie jest samodzielnie kompilowalne bez dwóch plików PNG:",
        "   `fractal_inpdep_results.png` i `fractal_real_images_results.png`.",
        "",
        "## Status",
        "",
        "Audyt strukturalny źródła zakończony. Następny etap to ekstrakcja pierwszego",
        "pakietu wykonawczego B-001--B-009 bez modernizacji historycznego kodu.",
    ]
    REPORT_OUT.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    print(
        f"LATEX AUDIT PASS: chapters={chapters}; tables={tables}; "
        f"listings={len(listings)}; verbatim={len(verbatim)}; "
        f"missing_assets={len(missing_assets)}"
    )


if __name__ == "__main__":
    main()
