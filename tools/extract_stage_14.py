#!/usr/bin/env python3
"""Wyodrębnij pozycje 100--108 i zachowaj faktyczne granice kodu."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "12_moe_evolution"

EXACT_HASHES = {
    65: "6784039bb6215563223dd30722a20e396ffc12692da8cfb2cdd4593e381ab52b",
    66: "d0f292652220f876b7aecd167d38de06a3cbf8eb8256dd49bda37c6688b10874",
    67: "2794c75cfa10c2b2de28030c6100d2a466351d6517234706089292a40b734a94",
    68: "96f1383ce8e846f78f23ad6fe61338e1ecda159e80acb0c67aee4b7212d2ba72",
    69: "c2008d55994e73dcc92a4ef484fa3d45ff257ceb8593749905ac86e461733338",
}
SEMANTIC_HASHES = {
    65: "512ed7e56b3f965c8ee81a2c192b18e1b731955a835359c9eb44cf5a24276e55",
    66: "ae303d1b93ebf186811214b7f069e6ebb51f8457ade4be3429309240ce96b5d8",
    67: "37d432f7445c48a5676960b4cd42fd5cc7145885d585eb0c9dc65bb4ac7ec0a2",
    68: "6e5dcd296a60ac9dcf1df230f3565ce582f69eaf8b9f5c0d59013c76885b1db9",
    69: "0a13a1cbc6fbf973c397baba47554905077c73106bd3ccfa2df768e8edad9246",
}

SEQUENCE = [
    ("MOE-001", 100, 65, [77, 78, 80],
     "Partial Unfreeze + MoE", "SOURCE_FRAGMENT_ONLY", None),
    ("MOE-009", 101, 65, [79, 80],
     "Partial Unfreeze + MoE — test trzech domen", "SOURCE_FRAGMENT_ONLY", None),
    ("MOE-002", 102, 66, [81, 83],
     "Sparse MoE + Gate Specialization Loss", "SOURCE_FRAGMENT_ONLY", None),
    ("MOE-003", 103, 66, [82],
     "Sparse MoE — sweep lambda_spec", "SOURCE_FRAGMENT_ONLY", None),
    ("MOE-004", 104, 67, [84, 85, 86],
     "Hard Assignment + Gate Distillation", "FULL", "hard_assign"),
    ("MOE-005", 105, 68, [87, 88, 91],
     "LayerNorm vs BatchNorm", "SHARED_LISTING_TARGET_CODE_ABSENT", None),
    ("MOE-006", 106, 68, [89],
     "Confidence routing", "FULL_SHARED_LISTING", "confidence"),
    ("MOE-007", 107, 68, [90],
     "Shared Expert — wynik negatywny", "SHARED_LISTING_TARGET_CODE_ABSENT", None),
    ("MOE-008", 108, 69, [92, 93, 94],
     "Hybrid BN/LN", "FULL", "hybrid"),
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
    try:
        tree = StripDocstrings().visit(ast.parse(text))
    except SyntaxError:
        return ""
    ast.fix_missing_locations(tree)
    payload = ast.dump(tree, annotate_fields=True, include_attributes=False)
    return sha(payload)


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
        result.append({"start": start + 1, "end": i + 1, "text": text,
                       "sha256": sha(text), "semantic_sha256": semantic_sha(text)})
        i += 1
    return result


def table_blocks(lines: list[str]) -> list[tuple[str, int, int]]:
    result = []
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("\\begin{table}"):
            i += 1
            continue
        start = i
        while i < len(lines) and not lines[i].lstrip().startswith("\\end{table}"):
            i += 1
        if i == len(lines):
            raise SystemExit("Niezamknieta tabela")
        result.append(("\n".join(lines[start:i + 1]), start + 1, i + 1))
        i += 1
    return result


def select_tables(all_tables, table_numbers):
    selected = []
    for number in table_numbers:
        if number < 1 or number > len(all_tables):
            raise SystemExit(f"Brak tabeli nr {number}; źródło zawiera {len(all_tables)} tabel")
        selected.append(all_tables[number - 1])
    return "\n\n".join(item[0] for item in selected), selected[0][1], selected[-1][2]


def runner(experiment_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_14.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main() -> int:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks = listing_blocks(lines)
    tables = table_blocks(lines)
    if len(blocks) != 74:
        raise SystemExit("Struktura zrodla LaTeX zmienila sie")
    for number, expected in EXACT_HASHES.items():
        block = blocks[number - 1]
        if block["sha256"] == expected:
            continue
        if block["semantic_sha256"] != SEMANTIC_HASHES[number]:
            raise SystemExit(f"Niezgodny kod semantyczny listingu {number}")
        print(f"SOURCE VARIANT: listing {number} ma inny komentarz/docstring; kod semantyczny zgodny")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "# Etap 14 — ewolucja MoE\n\n"
        "Pozycje 100–108 zachowują kolejność PDF-a. Sześć jednostek pozostaje "
        "audytem z powodu braku pętli docelowych; trzy jednostki wykonują pełne "
        "historyczne listingi 67–69.\n", encoding="utf-8")

    for position, (eid, order, listing, table_numbers, title, code_level, program) in enumerate(SEQUENCE, 1):
        base = OUT / eid
        historical = base / "historical"
        run = base / "runner"
        historical.mkdir(parents=True, exist_ok=True)
        run.mkdir(parents=True, exist_ok=True)
        block = blocks[listing - 1]
        executable = program is not None
        source_name = "source_from_monograph.py" if executable else (
            "shared_listing_context_from_monograph.py"
            if code_level == "SHARED_LISTING_TARGET_CODE_ABSENT"
            else "source_fragment_from_monograph.py"
        )
        (historical / source_name).write_text(block["text"] + "\n", encoding="utf-8", newline="\n")
        reported, start, end = select_tables(tables, table_numbers)
        result_name = "reported_result_from_monograph.tex"
        (historical / result_name).write_text(reported.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        execution_mode = "HISTORICAL_SHARED_SOURCE_WITH_COMPATIBILITY" if executable else "AUDIT_REPORTED_RESULT_SOURCE_BOUNDARY"
        provenance = {
            "experiment_id": eid,
            "source_sequence_in_stage": position,
            "source_order_in_monograph": order,
            "canonical_source": "docs/source/BOHN_PL.pdf",
            "extraction_source": "docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level": code_level,
            "execution_mode": execution_mode,
            "listing_indices": [listing],
            "reported_table_indices": table_numbers,
            "listing_target_code_present": executable,
            "historical_source_files": [source_name],
            "historical_source_sha256": [block["sha256"]],
            "historical_source_semantic_sha256": [block["semantic_sha256"]],
            "historical_source_line_ranges": [[block["start"], block["end"]]],
            "reported_result_file": result_name,
            "reported_result_start_line": start,
            "reported_result_end_line": end,
            "reported_result_sha256": sha(reported.rstrip("\n")),
            "historical_code_modified": False,
            "runtime_program": program,
            "runtime_compatibility": ["redirect_absolute_tmp_data_in_runtime_copy_only"] if executable else [],
        }
        (base / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if executable:
            boundary = (f"Listing {listing} zawiera wykonywalną pętlę tej jednostki. "
                        "Oryginał pozostaje niezmieniony; tylko `/tmp/data` jest przekierowane w kopii roboczej.")
        elif code_level == "SHARED_LISTING_TARGET_CODE_ABSENT":
            boundary = (f"Listing {listing} jest wspólnym kontekstem, ale nie wykonuje pętli generującej tę tabelę. "
                        "Jednostka pozostaje audytem wyniku raportowanego.")
        else:
            boundary = (f"Listing {listing} publikuje architekturę i funkcje, lecz nie uruchamia eksperymentu tej tabeli. "
                        "Jednostka pozostaje audytem wyniku raportowanego.")
        (base / "README_PL.md").write_text(
            f"# {eid} — {title}\n\nPozycja Etapu 14: **{position}/9**; chronologia monografii: **{order}/115**.\n\n{boundary}\n",
            encoding="utf-8")
        (run / "run.py").write_text(runner(eid), encoding="utf-8")

    print("EXTRACTION PASS: 9 Stage 14 units in original PDF chronology")
    print("SOURCE BOUNDARY: 6 audited-only units; 3 executable units from listings 67-69")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
