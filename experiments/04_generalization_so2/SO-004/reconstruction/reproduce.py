#!/usr/bin/env python3
"""Rekonstrukcja SO-004: współczynniki Fouriera profilu asymetrii."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import asymmetry_profile


points = [np.array([3.0, 4.0]), np.array([0.0, 5.0])]
thetas = np.linspace(0.0, 2.0 * np.pi, 200000, endpoint=False)
profiles = [asymmetry_profile(point, thetas) for point in points]

print("   n |    |c_n(x1)|    |c_n(x2)|      difference")
print("---------------------------------------------")
for order in range(-4, 5):
    kernel = np.exp(-1j * order * thetas)
    values = [abs(np.mean(profile * kernel)) for profile in profiles]
    print(f"{order:4d} | {values[0]:12.6f} {values[1]:12.6f} {abs(values[0]-values[1]):12.2e}")
