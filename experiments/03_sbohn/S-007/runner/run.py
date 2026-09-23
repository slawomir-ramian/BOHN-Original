#!/usr/bin/env python3
"""Uruchom S-007 przez wspólny runner Etapu 04."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_04.py"), "--only", "S-007"],
    cwd=ROOT,
))
