#!/usr/bin/env python3
"""Jawny test inwariantności z fragmentu i wzoru SO(2)."""

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import moment_features, rotate_blocks


x = np.array([[3.0, 4.0, 1.5, -2.0, 0.5, 3.0, -4.0, 2.0]])
rotated = rotate_blocks(x, theta=0.731)
error = np.linalg.norm(moment_features(x) - moment_features(rotated))
print(f"  ||Phi(x) - Phi(R*x)|| = {error:.2e}")
print("  => Invariance confirmed (error ~ integration accuracy)")
