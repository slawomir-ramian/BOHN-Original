#!/usr/bin/env python3
"""Jawna rekonstrukcja brakującego protokołu klasyfikacji SO-006."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.so2 import classification_scores


scores = classification_scores(n_blocks=4)
print("Method                                Accuracy")
print("-----------------------------------------------")
print(f"  Raw coordinates (x1..x8)              {scores['raw_logistic']:.3f}")
print(f"  SO(2)-SBOHN (4 blocks, M_1..M_4)      {scores['feature_logistic']:.3f}")
