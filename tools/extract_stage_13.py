#!/usr/bin/env python3
"""Wyodrębnij pozycje 90–99 i zachowaj faktyczne granice kodu."""
from __future__ import annotations

import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "11_integrated_system"
HASHES = {
    62: {"c825116384be142633eb3d07611ff7b3fc63f405a737788cbc6861965127cae4"},
    # Dwa audytowane warianty różnią się wyłącznie językiem trzech linii
    # docstringa: polskim w paczce bazowej i angielskim w źródle użytkownika.
    63: {
        "81a87df203c20fc983e66da6faad56b5b7e16a15d54991b50cf1c33922caee19",
        "28c817f5305580e65c75cf03281cccc70689307f2304617fc135099bd7c96de4",
    },
    64: {"18a059f09e0fd4b97f761077880459c0df2feabe9d0fbfca6996e3ac5ab7e288"},
}
SEQUENCE = [
    ("SYS-001", 90, 62, ["tab:meta_perm_gen_results"], "Meta-learned Permutation Generator", False),
    ("SYS-002", 91, 62, ["tab:moe_routing_results", "tab:moe_routing_distribution"], "Multi-task MoE Routing", False),
    ("SYS-003", 92, 62, ["tab:deep_vs_shallow", "tab:deep_fewshot"], "Deep Encoder", False),
    ("SYS-004", 93, 62, ["tab:partial_unfreeze", "tab:partial_unfreeze_delta"], "Partial Unfreeze", False),
    ("SYS-005", 94, 63, ["tab:integrated_fashion", "tab:integrated_router", "tab:integrated_endtoend", "tab:integrated_sizes"], "System zintegrowany", False),
    ("CPU-001", 95, 64, ["tab:cpu_exp1"], "Shallow vs Deep Encoder", True),
    ("CPU-002", 96, 64, ["tab:cpu_exp2", "tab:cpu_exp2_routing"], "MoE Multi-Domain Routing", True),
    ("CPU-003", 97, 64, ["tab:cpu_exp3"], "Cross-Domain Meta-Generator", True),
    ("CPU-004", 98, 64, ["tab:cpu_exp4_fashion", "tab:cpu_exp4_mnist"], "Partial Unfreeze — accuracy vs forgetting", True),
    ("CPU-005", 99, 64, ["tab:cpu_exp5"], "Few-Shot Scaling", True),
]


def sha(text): return hashlib.sha256(text.encode()).hexdigest()


def listing_blocks(lines):
    result=[]; i=0
    while i < len(lines):
        if "\\begin{lstlisting}" not in lines[i]: i += 1; continue
        start=i; i+=1; content=[]
        while i < len(lines) and "\\end{lstlisting}" not in lines[i]: content.append(lines[i]); i+=1
        if i == len(lines): raise SystemExit("Niezamkniety listing")
        text="\n".join(content); result.append({"start":start+1,"end":i+1,"text":text,"sha256":sha(text)}); i+=1
    return result


def tables(lines):
    result=[]; i=0
    while i < len(lines):
        if not lines[i].lstrip().startswith("\\begin{table}"): i+=1; continue
        start=i
        while i < len(lines) and not lines[i].lstrip().startswith("\\end{table}"): i+=1
        if i == len(lines): raise SystemExit("Niezamknieta tabela")
        result.append(("\n".join(lines[start:i+1]),start+1,i+1)); i+=1
    return result


def select_tables(all_tables, labels):
    selected=[]
    for label in labels:
        matches=[x for x in all_tables if f"\\label{{{label}}}" in x[0]]
        if len(matches)!=1: raise SystemExit(f"Tabela {label}: znaleziono {len(matches)}")
        selected.append(matches[0])
    return "\n\n".join(x[0] for x in selected), selected[0][1], selected[-1][2]


def runner(experiment_id):
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_13.py"), "--only", "{experiment_id}"], cwd=ROOT))
'''


def main():
    lines=SOURCE.read_text(encoding="utf-8").splitlines(); blocks=listing_blocks(lines); all_tables=tables(lines)
    if len(blocks)!=74: raise SystemExit("Struktura zrodla LaTeX zmienila sie")
    for number,expected in HASHES.items():
        if blocks[number-1]["sha256"] not in expected: raise SystemExit(f"Niezgodny hash listingu {number}")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"README.md").write_text(
        "# Etap 13 — system zintegrowany i bateria CPU\n\n"
        "Pozycje 90–99 zachowują kolejność PDF-a. Listingi 62–63 publikują klasy, ale nie pętle "
        "generujące tabele SYS. Listing 64 jest wspólnym programem CPU-001–CPU-005.\n",encoding="utf-8")
    for position,(eid,order,listing,labels,title,executable) in enumerate(SEQUENCE,1):
        base=OUT/eid; hist=base/"historical"; run=base/"runner"; hist.mkdir(parents=True,exist_ok=True); run.mkdir(parents=True,exist_ok=True)
        block=blocks[listing-1]
        source_name="source_from_monograph.py" if executable else "source_fragment_from_monograph.py"
        (hist/source_name).write_text(block["text"]+"\n",encoding="utf-8",newline="\n")
        reported,start,end=select_tables(all_tables,labels); result_name="reported_result_from_monograph.tex"
        (hist/result_name).write_text(reported.rstrip("\n")+"\n",encoding="utf-8",newline="\n")
        provenance={
            "experiment_id":eid,"source_sequence_in_stage":position,"source_order_in_monograph":order,
            "canonical_source":"docs/source/BOHN_PL.pdf","extraction_source":"docs/source/BOHN_EN_SOURCE.tex",
            "source_code_level":"FULL_SHARED_LISTING" if executable else "SOURCE_FRAGMENT_ONLY",
            "execution_mode":"HISTORICAL_SHARED_SOURCE_WITH_COMPATIBILITY" if executable else "AUDIT_REPORTED_RESULT_SOURCE_FRAGMENT",
            "listing_indices":[listing],"listing_target_code_present":executable,
            "historical_source_files":[source_name],"historical_source_sha256":[block["sha256"]],
            "historical_source_line_ranges":[[block["start"],block["end"]]],
            "reported_result_file":result_name,"reported_result_start_line":start,"reported_result_end_line":end,
            "reported_result_sha256":sha(reported.rstrip("\n")),"historical_code_modified":False,
            "compatibility_changes":["redirect_absolute_tmp_paths_in_runtime_copy_only","inject_missing_gc_import_in_runtime_copy_only"] if executable else [],
            "source_defect":"uses_gc_collect_without_importing_gc" if executable else None,
        }
        (base/"provenance.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        boundary=(f"Listing {listing} jest pełnym wspólnym programem pięciu eksperymentów CPU. "
                  "Oryginał nie importuje `gc`; poprawka działa wyłącznie w kopii roboczej."
                  if executable else f"Listing {listing} publikuje definicje architektury, lecz nie pętle treningu i ewaluacji tej tabeli. Wynik pozostaje audytem, nie lokalną reprodukcją.")
        (base/"README_PL.md").write_text(f"# {eid} — {title}\n\nPozycja Etapu 13: **{position}/10**; chronologia monografii: **{order}/115**.\n\n{boundary}\n",encoding="utf-8")
        (run/"run.py").write_text(runner(eid),encoding="utf-8")
    print("EXTRACTION PASS: 10 Stage 13 units in original PDF chronology")
    print("SOURCE BOUNDARY: 5 audited SYS units; 5 executable CPU units from shared listing 64")
    print("SOURCE DEFECT: listing 64 uses gc.collect() without import gc")


if __name__=="__main__": main()
