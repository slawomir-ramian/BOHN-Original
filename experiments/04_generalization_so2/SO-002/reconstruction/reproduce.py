#!/usr/bin/env python3
"""Rekonstrukcja SO-002 z opublikowanego wzoru profilu asymetrii."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import analytical_profile, asymmetry_profile


x = np.array([3.0, 4.0])
degrees = np.array([0.0, 30.0, 60.0, 90.0, 120.0, 180.0, 270.0, 360.0])
thetas = np.deg2rad(degrees)
numeric = asymmetry_profile(x, thetas)
analytic = analytical_profile(np.linalg.norm(x), thetas)

print("     theta  A_x numeryczne  A_x analityczne         Blad")
print("-------------------------------------------------------")
for degree, num, ana in zip(degrees, numeric, analytic, strict=True):
    print(f"{degree:8.0f}d {num:15.6f} {ana:16.6f} {abs(num-ana):12.2e}")
