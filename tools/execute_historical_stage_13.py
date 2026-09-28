#!/usr/bin/env python3
"""Uruchom wspólny listing 64 przez jawną kopię zgodności."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments"/"11_integrated_system"/"CPU-001"


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--marker",type=Path,required=True); args=parser.parse_args()
    provenance=json.loads((BASE/"provenance.json").read_text(encoding="utf-8"))
    source=BASE/"historical"/"source_from_monograph.py"; original=source.read_text(encoding="utf-8")
    expected=provenance["historical_source_sha256"][0]
    if hashlib.sha256(original.rstrip("\n").encode()).hexdigest()!=expected: raise SystemExit("Historical source hash mismatch")
    cache=ROOT/"reproduced"/"stage_13_dataset_cache"; cache.mkdir(parents=True,exist_ok=True)
    runtime=ROOT/"reproduced"/"stage_13_runtime"; runtime.mkdir(parents=True,exist_ok=True)
    compatible=original.replace("'/tmp/data'",repr(str(cache)))
    if "import gc" not in compatible: compatible=compatible.replace("import time\n","import time\nimport gc\n",1)
    runtime_source=runtime/"listing_64_runtime_compatible.py"
    runtime_source.write_text(compatible,encoding="utf-8",newline="\n")
    runpy.run_path(str(runtime_source),run_name="__main__")
    if hashlib.sha256(source.read_text(encoding="utf-8").rstrip("\n").encode()).hexdigest()!=expected: raise SystemExit("Historical source changed")
    args.marker.parent.mkdir(parents=True,exist_ok=True); args.marker.write_text("PASS\n",encoding="utf-8")
    return 0


if __name__=="__main__": raise SystemExit(main())
