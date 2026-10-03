#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
arguments = list(sys.argv[1:])
if "--output" not in arguments:
    arguments.extend(["--output", str(ROOT / "reproduced" / "stage_16_unit" / "SOTA-002R_result.json")])
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_16_unit.py"), "--unit", "SOTA-002R", *arguments], cwd=ROOT))
