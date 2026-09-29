#!/usr/bin/env python3
"""Wyodrębnij pozycje 109--115 z końcowego wspólnego suite'u."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "13_rmig_meta_fbohn"
LISTING = 71
EXACT_HASH = "7c22f9b681a821e5e7be402b3173f909e0c30ffa50ac48ee8f2086af0c33da60"
SEMANTIC_HASH = "041056cbad10f46b00d7cd5d0561ab9aa3ed0c81d7d5ecefb08c9bc267f48152"

SEQUENCE = [
    ("RF-001", 109, "sec:rmig_fbohn_v1", "RMIG-FBOHN v1", "v1"),
    ("RF-002", 110, "sec:test_a_oor", "RMIG-FBOHN — test out-of-representation", "testA"),
    ("MF-001", 111, "sec:meta_fbohn_v1v2", "Meta-FBOHN v1 — global weighting", "v2"),
    ("MF-002", 112, "sec:meta_fbohn_v1v2", "Meta-FBOHN v2 — orbitwise weighting", "v2"),
    ("MF-003", 113, "sec:meta_fbohn_v3", "Meta-FBOHN v3 — Learned Orbit Mixing", "v3"),
    ("MF-004", 114, "sec:meta_fbohn_v4", "Meta-FBOHN v4 — Symbolic Orbit Composer", "v4"),
    ("MF-005", 115, "sec:meta_fbohn_v5", "Meta-FBOHN v5 — Symbolic Library Discovery", "v5"),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class StripDocstrings(ast.NodeTransformer):
    def _strip(self, node):
        node = self.generic_visit(node)
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                node.body = body[1:]
        return node

    visit_Module = _strip
    visit_FunctionDef = _strip
    visit_AsyncFunctionDef = _strip
    visit_ClassDef = _strip


def semantic_sha(text: str) -> str:
    tree = StripDocstrings().visit(ast.parse(text))
    ast.fix_missing_locations(tree)
    return sha(ast.dump(tree, annotate_fields=True, include_attributes=False))


def listing_blocks(lines: list[str]) -> list[dict]:
    result = []
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
            raise SystemExit("Niezamkniety listing")
        text = "\n".join(content)
        result.append({"start": start + 1, "end": i + 1, "text": text, "sha256": sha(text)})
        i += 1
    return result


def labelled_section(lines: list[str], label: str) -> tuple[str, int, int]:
    matches = [i for i, line in enumerate(lines) if f"\\label{{{label}}}" in line]
    if len(matches) != 1:
        raise SystemExit(f"Etykieta {label}: znaleziono {len(matches)}")
    anchor = matches[0]
    start = anchor
    while start >= 0 and not lines[start].lstrip().startswith("\\section{"):
        start -= 1
    if start < 0:
        raise SystemExit(f"Brak początku sekcji {label}")
    end = anchor + 1
    while end < len(lines) and not lines[end].lstrip().startswith("\\section{") and not lines[end].lstrip().startswith("\\chapter{"):
        end += 1
    text = "\n".join(lines[start:end]).rstrip()
    return text, start + 1, end


def runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_15.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> int:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    if len(blocks) != 74:
        raise SystemExit("Struktura zrodla LaTeX zmienila sie")
    block = blocks[LISTING - 1]
    if block["sha256"] != EXACT_HASH:
        if semantic_sha(block["text"]) != SEMANTIC_HASH:
            raise SystemExit("Niezgodny kod semantyczny listingu 71")
        print("SOURCE VARIANT: listing 71 ma inny komentarz/docstring; kod semantyczny zgodny")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 15 — RMIG-FBOHN i Meta-FBOHN\n\n"
        "Pozycje 109–115 zachowują końcową kolejność PDF-a. Wszystkie siedem "
        "jednostek współdzieli pełny historyczny listing 71.\n", encoding="utf-8")

    for position, (eid, order, label, title, program) in enumerate(SEQUENCE, 1):
        base = OUT / eid
        historical = base / "historical"
        run = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        run.mkdir(parents=True, exist_ok=True)
        source_name = "source_from_monograph.py"
        # Zachowaj dokładny blok listingu, łącznie z jego końcową pustą linią.
        (historical / source_name).write_text(block["text"], encoding="utf-8", newline="\n")
        reported, start, end = labelled_section(lines, label)
        result_name = "reported_result_from_monograph.tex"
        (historical / result_name).write_text(reported + "\n", encoding="utf-8", newline="\n")
        provenance = {
            "experiment_id": eid,
            "source_sequence_in_stage": position,
            "source_order_in_monograph": order,
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": "FULL_SUITE",
            "execution_mode": "HISTORICAL_SUITE_FUNCTIONS_WITH_CELL_CHECKPOINTS",
            "listing_indices": [LISTING],
            "historical_source_files": [source_name],
            "historical_source_sha256": [block["sha256"]],
            "historical_source_semantic_sha256": [semantic_sha(block["text"])],
            "historical_source_line_ranges": [[block["start"], block["end"]]],
            "reported_result_file": result_name,
            "reported_result_start_line": start,
            "reported_result_end_line": end,
            "reported_result_sha256": sha(reported),
            "historical_code_modified": False,
            "runtime_program": program,
            "runtime_compatibility": ["cell_level_checkpoint_wrapper_without_source_changes"],
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (base / "README_PL.md").write_text(
            f"# {eid} — {title}\n\n"
            f"Pozycja Etapu 15: **{position}/7**; chronologia monografii: **{order}/115**.\n\n"
            "Jednostka korzysta z pełnego wspólnego listingu 71. Oryginalne źródło "
            "pozostaje niezmienione, a wrapper dodaje wyłącznie checkpointy komórek.\n",
            encoding="utf-8")
        (run / "run.py").write_text(runner(eid), encoding="utf-8")

    print("EXTRACTION PASS: 7 Stage 15 units in original PDF chronology")
    print("SOURCE BOUNDARY: 7 executable units from complete shared listing 71")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
