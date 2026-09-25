#!/usr/bin/env python3
"""Szybkie sondy techniczne Etapu 06."""
import argparse, importlib.util, sys, warnings
from pathlib import Path
import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from bohn_original.symmetry_discovery import flip_horizontal,rotate_180,random_permutation,asymmetry
BASE=ROOT/"experiments"/"04_symmetry_discovery"
def load(exp):
    p=BASE/exp/"historical"/"source_from_monograph.py"; s=importlib.util.spec_from_file_location(exp.replace("-","_"),p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def sd001():
    r=load("SD-001").run_one(0,2); names=["shift_up","shift_down","shift_left","shift_right"]; w=max(names,key=lambda n:r[n])
    print(f"baseline={r['baseline']:.4f}\nbest_structured={w}\nbest_net={r[w+'_net_mean']:.4f}")
def sd003():
    r=load("SD-003").run_one(0,2); w=r.iloc[0]["candidate"]; rank=int(r.index[r["candidate"]=="flip_horizontal"][0])+1
    print(f"winner={w}\nflip_horizontal_rank={rank}")
    if w!="flip_horizontal" or rank!=1: raise SystemExit("Sonda SD-003 nie rozpoznała symetrii")
def asd001():
    X=load_digits().data.astype(float); A=asymmetry(X,rotate_180(X)); w=np.random.default_rng(42).standard_normal(64)
    y=(A@w>np.median(A@w)).astype(int); Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.3,random_state=0)
    tr={"flip_horizontal":asymmetry(Xtr,flip_horizontal(Xtr)),"rotate_180":asymmetry(Xtr,rotate_180(Xtr))}
    te={"flip_horizontal":asymmetry(Xte,flip_horizontal(Xte)),"rotate_180":asymmetry(Xte,rotate_180(Xte))}
    for i in range(5): tr[f"rand_{i}"]=asymmetry(Xtr,random_permutation(Xtr,i)); te[f"rand_{i}"]=asymmetry(Xte,random_permutation(Xte,i))
    names=sorted(tr); P=np.hstack([tr[n] for n in names]); Q=np.hstack([te[n] for n in names])
    model=LogisticRegression(C=.1,penalty="l1",solver="saga",max_iter=5000,random_state=0)
    with warnings.catch_warnings(): warnings.simplefilter("ignore"); model.fit(P,ytr)
    imp={n:float(np.abs(model.coef_[:,i*64:(i+1)*64]).sum()) for i,n in enumerate(names)}; rank=sorted(imp,key=imp.get,reverse=True)
    acc=model.score(Q,yte); print(f"accuracy={acc:.4f}\ntop1={rank[0]}\nflip_horizontal_rank={rank.index('flip_horizontal')+1}")
    if rank[0]!="rotate_180" or acc<.90: raise SystemExit("Sonda ASD nie rozpoznała obrotu")
PROBES={"SD-001":sd001,"SD-003":sd003,"ASD-001":asd001}
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--only",choices=PROBES,required=True); PROBES[p.parse_args().only]()
