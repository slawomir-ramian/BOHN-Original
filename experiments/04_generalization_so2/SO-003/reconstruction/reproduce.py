#!/usr/bin/env python3
"""Rekonstrukcja SO-003: momenty numeryczne i wzór z funkcją Beta."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import analytical_moment, analytical_profile


points = [(1.0, 0.0), (3.0, 4.0), (0.0, 2.0)]
thetas = np.linspace(0.0, 2.0 * np.pi, 100000, endpoint=False)

print("   Punkt     r |      M_1      M_2      M_3      M_4      M_5      M_6")
print("---------------------------------------------------------------------------")
max_error = 0.0
for a, b in points:
    radius = float(np.hypot(a, b))
    profile = analytical_profile(radius, thetas)
    numeric = [float(np.mean(profile ** order)) for order in range(1, 7)]
    analytic = [analytical_moment(radius, order) for order in range(1, 7)]
    max_error = max(max_error, max(abs(x - y) for x, y in zip(numeric, analytic, strict=True)))
    values = " ".join(f"{value:8.3f}" for value in numeric)
    print(f" ({a:4.1f},{b:4.1f}) {radius:3.1f} | {values}")
print("   Analytical:     (identical to 3 decimal places)")
if max_error > 1e-7:
    raise SystemExit(f"Moment verification failed: {max_error:.3e}")
