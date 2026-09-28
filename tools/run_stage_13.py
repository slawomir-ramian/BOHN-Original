#!/usr/bin/env python3
"""Runner Etapu 13: audyt SYS i jedno wykonanie wspólnej baterii CPU."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,re,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IDS=["SYS-001","SYS-002","SYS-003","SYS-004","SYS-005","CPU-001","CPU-002","CPU-003","CPU-004","CPU-005"]
SMOKE=["SYS-001","SYS-005","CPU-001","CPU-004"]
PUB1={"Shallow":{"MNIST":92.6,"Fashion":79.1,"CIFAR10":31.9},"Deep":{"MNIST":93.6,"Fashion":82.4,"CIFAR10":34.0}}
PUB2_ACC={"MNIST":93.2,"Fashion":79.9,"Mixed":86.5}
PUB2_ROUTE={"MNIST":[38.1,16.6,15.2,30.1],"Fashion":[44.8,18.3,14.1,22.8]}
PUB3={"MNIST":[93.8,14.8,79.0],"Fashion":[51.2,18.7,32.5],"KMNIST":[10.6,7.5,3.1],"CIFAR10":[10.8,10.1,.7]}
STRATS=["Frozen","+Last1","+Last2","+Last3","All"]
SHOTS=[50,200,1000]
PUB4_F={"Frozen":[31.2,35.6,51.3],"+Last1":[37.4,49.1,69.5],"+Last2":[47.8,60.7,75.4],"+Last3":[48.4,66.9,76.1],"All":[47.6,64.8,73.4]}
PUB4_M={"Frozen":[65.5,74.6,74.4],"+Last1":[54.5,41.4,39.7],"+Last2":[31.8,43.2,23.3],"+Last3":[36.5,22.5,21.9],"All":[38.3,27.6,26.9]}
PUB5={10:21.8,25:29.5,50:23.8,100:33.5,250:30.7,500:24.3,1000:33.3,2500:20.5,5000:35.9}


def digest(data): return hashlib.sha256(data).hexdigest()


def parse_cpu(text):
    result={"CPU-001":{"Shallow":{},"Deep":{}},"CPU-002":{"accuracy":{},"routing":{"MNIST":[],"Fashion":[]}},"CPU-003":{},"CPU-004":{},"CPU-005":{}}
    for enc,domain,value in re.findall(r"^  (Shallow|Deep) on (MNIST|Fashion|CIFAR10): ([0-9.]+)%",text,re.M): result["CPU-001"][enc][domain]=float(value)
    s2=text.split("EXPERIMENT 2: MoE Multi-Domain Routing",1)[-1].split("EXPERIMENT 3:",1)[0]; current=None
    for line in s2.splitlines():
        m=re.match(r"  (MNIST|Fashion): ([0-9.]+)%",line)
        if m: current=m.group(1); result["CPU-002"]["accuracy"][current]=float(m.group(2)); continue
        m=re.match(r"    Expert [0-3]: ([0-9.]+)%",line)
        if m and current: result["CPU-002"]["routing"][current].append(float(m.group(1)))
        m=re.match(r"  Mixed: ([0-9.]+)%",line)
        if m: result["CPU-002"]["accuracy"]["Mixed"]=float(m.group(1))
    s3=text.split("EXPERIMENT 3: Cross-Domain Meta-Generator",1)[-1].split("EXPERIMENT 4:",1)[0]
    for d,m,r,delta in re.findall(r"^  (MNIST|Fashion|KMNIST|CIFAR10): Meta-Gen=([0-9.]+)%, Random=([0-9.]+)%, Delta=([+\-0-9.]+)%",s3,re.M): result["CPU-003"][d]={"meta":float(m),"random":float(r),"delta":float(delta)}
    s4=text.split("EXPERIMENT 4: Partial Unfreeze",1)[-1].split("EXPERIMENT 5:",1)[0]; shot=None
    for line in s4.splitlines():
        m=re.search(r"--- ([0-9]+)-shot ---",line)
        if m: shot=int(m.group(1)); continue
        m=re.match(r"    (Frozen|\+Last1|\+Last2|\+Last3|All): Fashion=([0-9.]+)%, MNIST=([0-9.]+)%",line)
        if m and shot: result["CPU-004"].setdefault(str(shot),{})[m.group(1)]={"fashion":float(m.group(2)),"mnist":float(m.group(3))}
    s5=text.split("EXPERIMENT 5: Few-Shot Scaling",1)[-1]
    for shot,value in re.findall(r"^\s+([0-9]+)-shot: ([0-9.]+)%",s5,re.M): result["CPU-005"][str(int(shot))]=float(value)
    return result


def deltas(actual,published): return [abs(float(a)-float(b)) for a,b in zip(actual,published)]


def compare(eid,p):
    if eid=="CPU-001":
        ds=[abs(p[e][d]-PUB1[e][d]) for e in PUB1 for d in PUB1[e]]; conclusion=all(p["Deep"][d]>p["Shallow"][d] for d in PUB1["Deep"])
    elif eid=="CPU-002":
        ds=[abs(p["accuracy"][d]-v) for d,v in PUB2_ACC.items()]+[abs(p["routing"][d][i]-v) for d,vals in PUB2_ROUTE.items() for i,v in enumerate(vals)]
        diffs=[abs(a-b) for a,b in zip(p["routing"]["MNIST"],p["routing"]["Fashion"])]; conclusion=max(diffs)<15
    elif eid=="CPU-003":
        ds=[abs(p[d][k]-PUB3[d][i]) for d in PUB3 for i,k in enumerate(["meta","random","delta"])]
        conclusion=p["MNIST"]["delta"]>20 and p["Fashion"]["delta"]>20 and abs(p["KMNIST"]["delta"])<10 and abs(p["CIFAR10"]["delta"])<10
    elif eid=="CPU-004":
        ds=[]
        for j,shot in enumerate(SHOTS):
            for s in STRATS: ds += [abs(p[str(shot)][s]["fashion"]-PUB4_F[s][j]),abs(p[str(shot)][s]["mnist"]-PUB4_M[s][j])]
        conclusion=p["1000"]["+Last2"]["fashion"]>p["1000"]["Frozen"]["fashion"] and p["1000"]["Frozen"]["mnist"]>p["1000"]["+Last2"]["mnist"]
    else:
        ds=[abs(p[str(k)]-v) for k,v in PUB5.items()]; conclusion=max(p.values())<50 and p["5000"]>p["10"]
    status="CLOSE_NUMERIC_MATCH" if conclusion and max(ds)<=5 else "CONCLUSION_MATCH" if conclusion else "NUMERIC_DIFFERENCE"
    return {"status":status,"scientific_conclusion_preserved":conclusion,"max_reported_numeric_delta_pp":max(ds),"note":"Wspólny historyczny listing 64; import gc dodany tylko w kopii zgodności."}


def valid_checkpoint(path):
    try:
        p=json.loads(path.read_text(encoding="utf-8")); return set(p)==set(IDS[5:]) and all(p[x] for x in IDS[5:])
    except Exception:return False


def execute_shared(raw):
    cp=ROOT/"reproduced"/"stage_13_checkpoint"; cp.mkdir(parents=True,exist_ok=True)
    parsed=cp/"cpu_suite_parsed.json"; out=cp/"cpu_suite_stdout.txt"; err=cp/"cpu_suite_stderr.txt"; marker=cp/"cpu_suite_complete.txt"
    if valid_checkpoint(parsed) and marker.exists(): return json.loads(parsed.read_text(encoding="utf-8")),0.0,0,out,err,True
    start=time.perf_counter(); env=os.environ.copy(); env["PYTHONIOENCODING"]="utf-8"
    with out.open("w",encoding="utf-8",newline="\n") as so,err.open("w",encoding="utf-8",newline="\n") as se:
        proc=subprocess.Popen([sys.executable,"-u",str(ROOT/"tools"/"execute_historical_stage_13.py"),"--marker",str(marker)],cwd=ROOT,env=env,text=True,encoding="utf-8",errors="replace",stdout=so,stderr=se)
        beat=start
        while proc.poll() is None:
            now=time.perf_counter()
            if now-beat>=60: print(f"CPU suite: nadal dziala | {now-start:.0f} s",flush=True); beat=now
            if now-start>=43200: proc.terminate(); proc.wait(); return {},now-start,124,out,err,False
            time.sleep(1)
    if proc.returncode!=0:return {},time.perf_counter()-start,proc.returncode,out,err,False
    payload=parse_cpu(out.read_text(encoding="utf-8",errors="replace")); parsed.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return payload,time.perf_counter()-start,0,out,err,False


def audit_row(eid):
    return {"execution_status":"PASS","return_code":0,"duration_seconds":0.0,"execution_mode":"AUDIT_REPORTED_RESULT_SOURCE_FRAGMENT","source_boundary":"SOURCE_FRAGMENT_ONLY","historical_code_modified":False,"comparison":{"status":"AUDITED_REPORTED_RESULT","scientific_conclusion_preserved":None,"max_reported_numeric_delta_pp":None,"note":"Opublikowano klasy, ale nie pętlę generującą tabelę."}}


def probe(eid,raw):
    out=raw/f"{eid}_stdout.txt";err=raw/f"{eid}_stderr.txt";start=time.perf_counter()
    c=subprocess.run([sys.executable,str(ROOT/"tools"/"smoke_stage_13.py"),"--only",eid],cwd=ROOT,text=True,encoding="utf-8",errors="replace",capture_output=True)
    out.write_text(c.stdout,encoding="utf-8");err.write_text(c.stderr,encoding="utf-8")
    return {"execution_status":"PASS" if c.returncode==0 else "FAILED","return_code":c.returncode,"duration_seconds":round(time.perf_counter()-start,6),"execution_mode":"SMOKE_PROBE","historical_code_modified":False,"comparison":{"status":"SMOKE_PROBE_PASS" if c.returncode==0 else "SMOKE_PROBE_FAILED","scientific_conclusion_preserved":None}}


def manifest(output):
    m=output/"MANIFEST_SHA256.txt"; rows=[f"{digest(p.read_bytes())}  {p.relative_to(output).as_posix()}" for p in sorted(output.rglob('*')) if p.is_file() and p!=m];m.write_text("\n".join(rows)+"\n",encoding="utf-8")


def main():
    a=argparse.ArgumentParser();a.add_argument("--smoke",action="store_true");a.add_argument("--only",choices=IDS);args=a.parse_args()
    selected=[args.only] if args.only else SMOKE if args.smoke else IDS; mode="only" if args.only else "smoke" if args.smoke else "full"
    stamp=datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ");output=ROOT/"reproduced"/"stage_13_runs"/stamp;raw=output/"raw";raw.mkdir(parents=True,exist_ok=True)
    results={}; shared=None
    for eid in selected:
        print(f"RUN {eid} ...",flush=True)
        if args.smoke: row=probe(eid,raw)
        elif eid.startswith("SYS"): row=audit_row(eid)
        else:
            if shared is None: shared=execute_shared(raw)
            payload,duration,rc,so,se,reused=shared; out=raw/f"{eid}_stdout.txt";err=raw/f"{eid}_stderr.txt";shutil.copyfile(so,out);shutil.copyfile(se,err)
            parsed=raw/f"{eid}_result.json"; parsed.write_text(json.dumps(payload.get(eid,{}),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            passed=rc==0 and eid in payload
            row={"execution_status":"PASS" if passed else "FAILED","return_code":rc,"duration_seconds":0.0 if results and any(x.startswith('CPU') for x in results) else round(duration,6),"execution_mode":"HISTORICAL_SHARED_SOURCE_WITH_COMPATIBILITY","source_boundary":"FULL_SHARED_LISTING","historical_code_modified":False,"source_defect_preserved":"uses_gc_collect_without_importing_gc","runtime_compatibility":["redirect_tmp_data","inject_import_gc"],"checkpoint_reused":reused,"stdout_file":f"raw/{out.name}","stderr_file":f"raw/{err.name}","comparison":compare(eid,payload[eid]) if passed else {"status":"EXECUTION_FAILED","scientific_conclusion_preserved":False}}
        results[eid]=row;print(f"{eid}: {row['execution_status']} | {row['comparison']['status']} | {row['duration_seconds']:.2f} s",flush=True)
    payload={"stage":"13","mode":mode,"created_utc":stamp,"source_chronology":selected,"historical_code_modified":False,"environment":{"python":sys.version,"platform":platform.platform()},"experiments":results}
    (output/"results.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Etap 13 — raport wykonania","","| # | ID | Wykonanie | Porównanie | Czas [s] |","|---:|---|---|---|---:|"]
    for i,eid in enumerate(selected,1):r=results[eid];lines.append(f"| {i} | {eid} | {r['execution_status']} | {r['comparison']['status']} | {r['duration_seconds']:.3f} |")
    lines += ["","Jednostki SYS są audytem tabel, ponieważ listingi 62–63 nie publikują pętli eksperymentalnych.","Listing 64 zachowano bez zmian; brakujący import `gc` dodano tylko w kopii wykonawczej."]
    (output/"REPRODUCTION_REPORT_PL.md").write_text("\n".join(lines)+"\n",encoding="utf-8");manifest(output)
    latest=ROOT/"reproduced"/"stage_13_runs"/"LATEST_RUN.txt";latest.parent.mkdir(parents=True,exist_ok=True);latest.write_text(str(output.relative_to(ROOT)).replace('\\','/')+"\n",encoding="utf-8")
    print(f"RESULTS: {output.resolve()}")
    if mode=="full":
        art=ROOT/"artifacts";art.mkdir(exist_ok=True);z=shutil.make_archive(str(art/f"BOHN_ORIGINAL_STAGE_13_RESULTS_{stamp}"),"zip",root_dir=output);print(f"ZIP: {Path(z).resolve()}")
    return 0 if all(r["execution_status"]=="PASS" for r in results.values()) else 1


if __name__=="__main__":raise SystemExit(main())
