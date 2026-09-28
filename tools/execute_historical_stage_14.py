#!/usr/bin/env python3
"""Uruchom pełny listing Etapu 14 przez jawną kopię zgodności."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = {
    "hard_assign": ("MOE-004", 67),
    "confidence": ("MOE-006", 68),
    "hybrid": ("MOE-008", 69),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", choices=PROGRAMS, required=True)
    parser.add_argument("--marker", type=Path, required=True)
    args = parser.parse_args()
    experiment_id, listing = PROGRAMS[args.program]
    base = ROOT / "experiments" / "12_moe_evolution" / experiment_id
    provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
    source = base / "historical" / "source_from_monograph.py"
    original = source.read_text(encoding="utf-8")
    expected = provenance["historical_source_sha256"][0]
    if hashlib.sha256(original.rstrip("\n").encode()).hexdigest() != expected:
        raise SystemExit("Historical source hash mismatch")

    previous_cache = ROOT / "reproduced" / "stage_13_dataset_cache"
    cache = previous_cache if previous_cache.is_dir() else ROOT / "reproduced" / "stage_14_dataset_cache"
    cache.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / "reproduced" / "stage_14_runtime" / args.program
    runtime.mkdir(parents=True, exist_ok=True)
    compatible = original.replace("'/tmp/data'", repr(str(cache))).replace('"/tmp/data"', repr(str(cache)))
    runtime_source = runtime / f"listing_{listing}_runtime_compatible.py"
    runtime_source.write_text(compatible, encoding="utf-8", newline="\n")

    previous_cwd = Path.cwd()
    try:
        os.chdir(runtime)
        runpy.run_path(str(runtime_source), run_name="__main__")
    finally:
        os.chdir(previous_cwd)

    if hashlib.sha256(source.read_text(encoding="utf-8").rstrip("\n").encode()).hexdigest() != expected:
        raise SystemExit("Historical source changed")
    args.marker.parent.mkdir(parents=True, exist_ok=True)
    args.marker.write_text("PASS\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
