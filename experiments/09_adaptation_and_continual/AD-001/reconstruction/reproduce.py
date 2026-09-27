#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools" / "run_stage_11.py"), "--only", "AD-001"], cwd=ROOT))
