#!/usr/bin/env python3
"""Uruchom Etap 06 w kolejności PDF-a z checkpointem i heartbeat."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/"experiments"/"04_symmetry_discovery"
SOURCE_CHRONOLOGY=["SD-001","SD-002","SD-003","SD-004","ASD-001"]
SMOKE=["SD-001","SD-003","ASD-001"]
EXPECTED={
"SD-001":{"baseline":.7409,"random":.7961,"best":.8244,"left_acc":.831975,"left_net":.035883,"right_acc":.831358,"right_net":.035265},
"SD-002":{"baseline":.5005,"random":.5012,"best":.5283,"left_acc":.501667,"left_net":.000417},
"SD-003":{"baseline":.7567,"random":.7845,"target_acc":.959506,"target_net":.175052},
"SD-004":{"baseline":.7515,"random":.7925,"target_acc":.964568,"target_net":.172102},
"ASD-001":{"0.02":.9244,"0.05":.9554,"0.10":.9630,"0.20":.9630}}
def digest(b): return hashlib.sha256(b).hexdigest()
def control(text,label):
    m=re.search(rf"^{re.escape(label)}\s*([0-9.]+)",text,re.M)
    if not m: raise ValueError(label)
    return float(m.group(1))
def row(text,name):
    m=re.search(rf"^\s*{re.escape(name)}\s+(.+)$",text,re.M)
    if not m: raise ValueError(name)
    return [float(x) for x in re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?",m.group(1))]
def result(status,ok,actual,deltas,note):
    return {"status":status,"scientific_conclusion_preserved":ok,"max_reported_numeric_delta":max(deltas,default=0.0),"actual_summary":actual,"note":note}
def compare_shift(text,negative=False):
    exp="SD-002" if negative else "SD-001"; e=EXPECTED[exp]
    actual={"baseline":control(text,"baseline mean:"),"random":control(text,"random mean:"),"best":control(text,"random best mean:")}
    candidates={}
    for n in ["shift_left","shift_right","shift_up","shift_down"]:
        v=row(text,n); candidates[n]={"acc":v[0],"net":v[3],"positive":int(v[5])}
    actual["candidates"]=candidates; actual["left_acc"]=candidates["shift_left"]["acc"]; actual["left_net"]=candidates["shift_left"]["net"]
    if negative:
        ok=.45<=actual["baseline"]<=.55 and .45<=actual["random"]<=.55 and max(abs(v["net"]) for v in candidates.values())<.01
        note="Losowe etykiety pozostają na poziomie przypadku."
    else:
        actual["right_acc"]=candidates["shift_right"]["acc"]; actual["right_net"]=candidates["shift_right"]["net"]
        ok=all(candidates[n]["net"]>0 and candidates[n]["positive"]==30 for n in ["shift_left","shift_right"])
        note="Poziome przesunięcia zachowują dodatni net score w 30/30 seedach."
    d=[abs(actual[k]-v) for k,v in e.items()]; status="CLOSE_NUMERIC_MATCH" if ok and max(d)<=.002 else ("CONCLUSION_MATCH" if ok else "SCIENTIFIC_MISMATCH")
    return result(status,ok,actual,d,note)
def compare_hidden(text,exp,target):
    e=EXPECTED[exp]; v=row(text,target); actual={"baseline":control(text,"Baseline mean:"),"random":control(text,"Random mean:"),"target_acc":v[0],"target_net":v[4]}
    w=re.search(rf"Best candidate per seed:\s*(?:candidate\s*)?{re.escape(target)}\s+(\d+)",text,re.M); b=re.search(r"Best rank count:\s*(\d+)\s*/\s*(\d+)",text)
    actual["winner_count"]=int(w.group(1)) if w else 0; actual["best_rank"]=[int(b.group(1)),int(b.group(2))] if b else [0,0]
    ok=actual["winner_count"]==30 and actual["best_rank"]==[30,30]; d=[abs(actual[k]-v) for k,v in e.items()]
    status="CLOSE_NUMERIC_MATCH" if ok and max(d)<=.002 else ("CONCLUSION_MATCH" if ok else "SCIENTIFIC_MISMATCH")
    return result(status,ok,actual,d,f"{target}: ranga 1 w 30/30 seedach.")
def compare_asd(text):
    pat=re.compile(r"=== C = ([0-9.]+) ===.*?Accuracy:\s*([0-9.]+).*?Top1 True:\s*(\d+)/(\d+).*?Both True Top10:\s*(\d+)/(\d+).*?Mean Best Rank:\s*([0-9.]+).*?Mean Worst Rank:\s*([0-9.]+)",re.S)
    rows={}
    for m in pat.finditer(text):
        c=f"{float(m.group(1)):.2f}"; rows[c]={"accuracy":float(m.group(2)),"top1":[int(m.group(3)),int(m.group(4))],"top10":[int(m.group(5)),int(m.group(6))],"best":float(m.group(7)),"worst":float(m.group(8))}
    if set(rows)!=set(EXPECTED["ASD-001"]): raise ValueError("brak wierszy ASD")
    ok=all(v["top1"]==[10,10] and v["top10"]==[10,10] and v["best"]==1 and v["worst"]==2 for v in rows.values())
    d=[abs(rows[c]["accuracy"]-v) for c,v in EXPECTED["ASD-001"].items()]
    status="CLOSE_NUMERIC_MATCH" if ok and max(d)<=.002 else ("CONCLUSION_MATCH" if ok else "SCIENTIFIC_MISMATCH")
    return result(status,ok,rows,d,"Rangi kandydatów sprawdzone dla 4 wartości C.")
def compare(exp,text):
    try:
        if exp=="SD-001": return compare_shift(text)
        if exp=="SD-002": return compare_shift(text,True)
        if exp=="SD-003": return compare_hidden(text,exp,"flip_horizontal")
        if exp=="SD-004": return compare_hidden(text,exp,"rotate_180")
        return compare_asd(text)
    except (ValueError,IndexError) as exc: return result("UNPARSEABLE_OUTPUT",False,{},[],str(exc))
def command(exp,smoke):
    return [sys.executable,str(ROOT/"tools"/"smoke_stage_06.py"),"--only",exp] if smoke else [sys.executable,"-u",str(BASE/exp/"historical"/"source_from_monograph.py")]
def run_unit(exp,raw,smoke=False):
    out,err=raw/f"{exp}_stdout.txt",raw/f"{exp}_stderr.txt"; start=time.perf_counter(); env=os.environ.copy(); env["PYTHONIOENCODING"]="utf-8"; timed=False
    with out.open("w",encoding="utf-8",newline="\n") as oh,err.open("w",encoding="utf-8",newline="\n") as eh:
        p=subprocess.Popen(command(exp,smoke),cwd=ROOT,env=env,text=True,encoding="utf-8",errors="replace",stdout=oh,stderr=eh); notice=start
        try:
            while p.poll() is None:
                now=time.perf_counter()
                if now-notice>=60: print(f"{exp}: nadal działa | {now-start:.0f} s",flush=True); notice=now
                if now-start>=14400:
                    timed=True; p.terminate()
                    try: p.wait(30)
                    except subprocess.TimeoutExpired: p.kill(); p.wait()
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            p.terminate()
            try: p.wait(10)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
            raise
        rc=p.returncode
        if timed: eh.write("\n[RUNNER_TIMEOUT] Przekroczono 14400 s.\n")
    stdout=out.read_text(encoding="utf-8",errors="replace"); stderr=err.read_text(encoding="utf-8",errors="replace")
    if timed:
        cmp=result("TIMEOUT",False,{},[],"Techniczny limit czasu; nie jest to wynik merytoryczny.")
    elif smoke:
        cmp={"status":"SMOKE_PROBE_PASS" if rc==0 else "SMOKE_PROBE_FAILED","scientific_conclusion_preserved":None,"max_reported_numeric_delta":None,"actual_summary":{},"note":"Smoke nie zastępuje pełnego programu."}
    else:
        cmp=compare(exp,stdout)
    executed=(ROOT/"tools"/"smoke_stage_06.py") if smoke else (BASE/exp/"historical"/"source_from_monograph.py")
    status="TIMEOUT" if timed else ("PASS" if rc==0 else "FAILED")
    return {"execution_status":status,"return_code":rc,"duration_seconds":round(time.perf_counter()-start,6),"execution_mode":"SMOKE_PROBE" if smoke else "HISTORICAL_SOURCE","executed_file":str(executed.relative_to(ROOT)).replace("\\","/"),"stdout_sha256":digest(stdout.encode()),"stderr_sha256":digest(stderr.encode()),"stderr_nonempty":bool(stderr.strip()),"stdout_file":f"raw/{exp}_stdout.txt","stderr_file":f"raw/{exp}_stderr.txt","comparison":cmp}
def manifest(out):
    p=out/"MANIFEST_SHA256.txt"; lines=[]
    for f in sorted(out.rglob("*")):
        if f.is_file() and f!=p: lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(out).as_posix()}")
    p.write_text("\n".join(lines)+"\n",encoding="utf-8")
def report(payload):
    lines=["# Etap 06 - raport wykonania wykrywania symetrii","","Jednostki wykonano w kolejności PDF-a.","","| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |","|---:|---|---|---|---|---:|"]
    for i,e in enumerate(payload["source_chronology"],1):
        r=payload["experiments"][e]; lines.append(f"| {i} | {e} | {r['execution_mode']} | {r['execution_status']} | {r['comparison']['status']} | {r['duration_seconds']:.3f} |")
    lines += ["","Pełny przebieg wykonuje niezmieniony kod historyczny. ASD-001 używa solvera saga bez ustalonego random_state."]
    return "\n".join(lines)+"\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--smoke",action="store_true"); ap.add_argument("--only",choices=SOURCE_CHRONOLOGY); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    if a.only: selected=[a.only]; mode="only"; smoke=False
    elif a.smoke: selected=SMOKE; mode="smoke"; smoke=True
    else: selected=SOURCE_CHRONOLOGY; mode="full"; smoke=False
    now=datetime.now(timezone.utc).replace(microsecond=0); stamp=now.strftime("%Y%m%dT%H%M%SZ"); out=a.output_dir or ROOT/"reproduced"/"stage_06_runs"/stamp; raw=out/"raw"; raw.mkdir(parents=True,exist_ok=True); results={}
    for exp in selected:
        print(f"RUN {exp} ...",flush=True); r=run_unit(exp,raw,smoke); results[exp]=r; print(f"{exp}: {r['execution_status']} | {r['comparison']['status']} | {r['duration_seconds']:.2f} s",flush=True)
        (out/"CHECKPOINT.json").write_text(json.dumps({"stage":"06","run_utc":now.isoformat(),"mode":mode,"source_chronology":selected,"completed_units":list(results),"experiments":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    versions={}
    for m,n in [("numpy","numpy"),("pandas","pandas"),("sklearn","scikit_learn")]:
        try: versions[n]=__import__(m).__version__
        except ImportError: versions[n]=None
    payload={"stage":"06","run_utc":now.isoformat(),"mode":mode,"source_chronology":selected,"full_source_chronology":SOURCE_CHRONOLOGY,"environment":{"python":sys.version,"platform":platform.platform(),**versions,"processor_count":os.cpu_count()},"experiments":results}
    (out/"results.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); (out/"REPRODUCTION_REPORT_PL.md").write_text(report(payload),encoding="utf-8")
    latest=ROOT/"reproduced"/"stage_06_runs"/"LATEST_RUN.txt"; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_text((str(out.relative_to(ROOT)).replace("\\","/") if out.is_relative_to(ROOT) else str(out))+"\n",encoding="utf-8"); manifest(out)
    z=None
    if mode=="full":
        art=ROOT/"artifacts"; art.mkdir(exist_ok=True); z=Path(shutil.make_archive(str(art/f"BOHN_ORIGINAL_STAGE_06_RESULTS_{stamp}"),"zip",root_dir=out))
    print(f"RESULTS: {out}");
    if z: print(f"ZIP: {z}")
    return 1 if any(r["execution_status"]!="PASS" for r in results.values()) else 0
if __name__=="__main__": raise SystemExit(main())
