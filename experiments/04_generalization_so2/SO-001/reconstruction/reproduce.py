#!/usr/bin/env python3
"""Rekonstrukcja raportowania SO-001; historyczny listing nie drukuje tabeli."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import numerical_symmetrizer


points = [
    np.array([1.0, 0.0]),
    np.array([3.0, 4.0]),
    np.array([0.5, -2.0]),
    np.array([7.0, 7.0]),
]
sample_counts = [100, 1000, 10000, 100000]

print("        Point x |        N=100       N=1000      N=10000     N=100000")
print("----------------------------------------------------------------------")
for x in points:
    values = [np.linalg.norm(numerical_symmetrizer(x, n)) for n in sample_counts]
    print(
        f"  ({x[0]:5.1f},{x[1]:5.1f}) | "
        + " ".join(f"{value:12.2e}" for value in values)
    )
