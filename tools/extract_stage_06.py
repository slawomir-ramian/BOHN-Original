#!/usr/bin/env python3
"""Wyodrębnij Etap 06 w oryginalnej kolejności PDF-a."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "source" / "BOHN_EN_SOURCE.tex"
OUT = ROOT / "experiments" / "04_symmetry_discovery"
SEQUENCE = [
    {"id":"SD-001","order":29,"listing":41,"verbatim":9},
    {"id":"SD-002","order":30,"listing":42,"verbatim":10},
    {"id":"SD-003","order":31,"listing":43,"verbatim":11},
    {"id":"SD-004","order":32,"listing":44,"verbatim":12},
    {"id":"ASD-001","order":33,"listing":45,"table":"tab:l1summary"},
]
ASD_TABLE_HASH = "2b4b61c3d8a59d0df7e6efd63ffd876aa424bdfe6a5c77d809ebcbecaa704420"
ASD_TEXT = """C accuracy top1_true both_true_top10 mean_best_rank mean_worst_rank
0.02 0.9244 10/10 10/10 1.0 2.0
0.05 0.9554 10/10 10/10 1.0 2.0
0.10 0.9630 10/10 10/10 1.0 2.0
0.20 0.9630 10/10 10/10 1.0 2.0
"""

def blocks(lines, env):
    begin, end = f"\\begin{{{env}}}", f"\\end{{{env}}}"
    out=[]; i=0
    while i < len(lines):
        if begin not in lines[i]: i += 1; continue
        start=i; i += 1; content=[]
        while i < len(lines) and end not in lines[i]: content.append(lines[i]); i += 1
        if i == len(lines): raise SystemExit(f"Niezamknięty blok {env}")
        text="\n".join(content)
        out.append({"start":start+1,"end":i+1,"text":text,"hash":hashlib.sha256(text.encode()).hexdigest()})
        i += 1
    return out

def hashes(path):
    with path.open(encoding="utf-8",newline="") as f:
        return {int(r["index"]):r["sha256"] for r in csv.DictReader(f)}

def table(lines,label):
    marker=f"\\label{{{label}}}"; pos=lines.index(marker)
    start=max(i for i in range(pos+1) if lines[i].startswith("\\begin{table"))
    end=next(i for i in range(pos,len(lines)) if lines[i]=="\\end{table}")
    text="\n".join(lines[start:end+1])
    return {"start":start+1,"end":end+1,"text":text,"hash":hashlib.sha256(text.encode()).hexdigest()}

def runner(exp):
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,str(ROOT/"tools"/"run_stage_06.py"),"--only","{exp}"],cwd=ROOT))
'''

def main():
    lines=SOURCE.read_text(encoding="utf-8").splitlines()
    listings, verbatim=blocks(lines,"lstlisting"),blocks(lines,"verbatim")
    lh=hashes(ROOT/"inventory"/"latex_listing_map.csv")
    vh=hashes(ROOT/"inventory"/"latex_verbatim_map.csv")
    if len(listings)!=74 or len(verbatim)!=20: raise SystemExit("Struktura źródła zmieniona")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"README.md").write_text("# Etap 06 - wykrywanie symetrii\n\nJednostki `SD-001`--`SD-004` i `ASD-001` są zachowane w kolejności PDF-a.\n",encoding="utf-8")
    for position,item in enumerate(SEQUENCE,1):
        base=OUT/item["id"]; hist=base/"historical"; run=base/"runner"
        hist.mkdir(parents=True,exist_ok=True); run.mkdir(parents=True,exist_ok=True)
        src=listings[item["listing"]-1]
        if src["hash"]!=lh[item["listing"]]: raise SystemExit(f"Niezgodny hash {item['id']}")
        (hist/"source_from_monograph.py").write_text(src["text"]+"\n",encoding="utf-8",newline="\n")
        if "verbatim" in item:
            res=verbatim[item["verbatim"]-1]
            if res["hash"]!=vh[item["verbatim"]]: raise SystemExit(f"Niezgodny wynik {item['id']}")
            result_file="reported_results.txt"; kind="VERBATIM"
            (hist/result_file).write_text(res["text"]+"\n",encoding="utf-8",newline="\n")
            result_note=f"Wynik: blok `verbatim` {item['verbatim']} (wiersze {res['start']}--{res['end']})."
        else:
            res=table(lines,item["table"])
            if res["hash"]!=ASD_TABLE_HASH: raise SystemExit("Niezgodny hash tabeli ASD")
            result_file="reported_results_table.tex"; kind="TABLE_4.2"
            (hist/result_file).write_text(res["text"]+"\n",encoding="utf-8",newline="\n")
            (hist/"reported_results.txt").write_text(ASD_TEXT,encoding="utf-8",newline="\n")
            result_note=f"Wynik: dokładna tabela 4.2 (wiersze {res['start']}--{res['end']}); TXT jest transkrypcją."
        prov={"experiment_id":item["id"],"source_sequence_in_stage":position,"source_order_in_monograph":item["order"],
              "canonical_source":"docs/source/BOHN_PL.pdf","extraction_source":"docs/source/BOHN_EN_SOURCE.tex",
              "source_code_level":"FULL_UNCAPTIONED","execution_mode":"HISTORICAL_SOURCE","listing_index":item["listing"],
              "latex_start_line":src["start"],"latex_end_line":src["end"],"historical_source_sha256":src["hash"],
              "reported_result_kind":kind,"reported_result_file":result_file,"reported_result_start_line":res["start"],
              "reported_result_end_line":res["end"],"reported_result_sha256":res["hash"],"historical_code_modified":False}
        (base/"provenance.json").write_text(json.dumps(prov,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        readme=f"""# {item['id']}

Pozycja Etapu 06: **{position}/5**; chronologia monografii: **{item['order']}/115**.

Pełny kod historyczny: `historical/source_from_monograph.py`, listing {item['listing']}
(wiersze {src['start']}--{src['end']}), wyodrębniony bez zmian. {result_note}

Pełny tryb wykonuje `HISTORICAL_SOURCE`. Smoke jest osobną sondą techniczną.
"""
        (base/"README_PL.md").write_text(readme,encoding="utf-8")
        (run/"run.py").write_text(runner(item["id"]),encoding="utf-8")
    print("EXTRACTION PASS: 5 Stage 06 units in original PDF chronology")
if __name__=="__main__": main()
