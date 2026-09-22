#!/usr/bin/env python3
"""Uruchom tylko B-005 przez wspólny, udokumentowany adapter."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_03.py"), "--only", "B-005"],
    cwd=ROOT,
))
