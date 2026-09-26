#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_07r.py"), "--only", "PL-002R"], cwd=ROOT))
