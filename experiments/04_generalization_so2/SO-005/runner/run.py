#!/usr/bin/env python3
"""Uruchom SO-005 przez wspólny runner Etapu 05."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call(
    [sys.executable, str(ROOT / "tools" / "run_stage_05.py"), "--only", "SO-005"],
    cwd=ROOT,
))
