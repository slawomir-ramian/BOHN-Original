#!/usr/bin/env python3
"""Wykonaj niezmieniony listing poprzez tymczasową kopię zgodności ścieżek."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "10_sota_and_scaling"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, choices=["SOTA-001", "SOTA-002"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    provenance = json.loads((BASE / args.id / "provenance.json").read_text(encoding="utf-8"))
    source = BASE / args.id / "historical" / "source_from_monograph.py"
    original = source.read_text(encoding="utf-8")
    actual_hash = hashlib.sha256(original.rstrip("\n").encode()).hexdigest()
    if actual_hash != provenance["historical_source_sha256"][0]:
        raise SystemExit("Historical source hash mismatch")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    runtime_root = ROOT / "reproduced" / "stage_12_runtime" / args.id
    runtime_root.mkdir(parents=True, exist_ok=True)
    dataset_root = ROOT / "reproduced" / "stage_12_dataset_cache"
    dataset_root.mkdir(parents=True, exist_ok=True)
    output_literal = "/tmp/sota_acc.json" if args.id == "SOTA-001" else "/tmp/sota_scaling.json"
    compatible = original.replace("'/tmp/data'", repr(str(dataset_root)))
    compatible = compatible.replace(repr(output_literal), repr(str(args.output.resolve())))
    runtime_source = runtime_root / "runtime_compatible_source.py"
    runtime_source.write_text(compatible, encoding="utf-8", newline="\n")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    runpy.run_path(str(runtime_source), run_name="__main__")
    if not args.output.is_file():
        raise SystemExit("Historical program did not create the expected JSON output")
    if hashlib.sha256(source.read_text(encoding="utf-8").rstrip("\n").encode()).hexdigest() != actual_hash:
        raise SystemExit("Historical source changed during execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
