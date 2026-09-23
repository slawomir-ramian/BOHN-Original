#!/usr/bin/env python3
"""Jawna rekonstrukcja brakującego protokołu klasyfikacji SO-005."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import classification_scores


scores = classification_scores(n_blocks=2)
print("Method                             LogReg   RandomForest")
print("--------------------------------------------------------")
print(f"  Raw coordinates (x1..x4)       {scores['raw_logistic']:.3f}          {scores['raw_forest']:.3f}")
print(f"  SO(2)-SBOHN (M_1..M_4)        {scores['feature_logistic']:.3f}          {scores['feature_forest']:.3f}")
print(f"  Oracle (r1, r2)                {scores['oracle_logistic']:.3f}            ---")
