#!/usr/bin/env python3
"""Szybkie sondy techniczne Etapu 07; nie zastępują pełnych eksperymentów."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.permutation_representation import (  # noqa: E402
    asymmetry,
    flip_horizontal,
    linear_cka,
    rotate_180,
    sum_asymmetry,
    z3_features,
    z3_permutation,
)

IDS = ["PL-001", "PL-002", "PL-003", "AR-001", "AR-002", "AR-003", "AR-004", "HD-001", "HD-002", "HD-003", "CMP-001", "CMP-002"]


def probe(experiment_id: str) -> dict:
    rng = np.random.default_rng(707)
    images = rng.normal(size=(24, 64))
    rot = rotate_180(np.arange(64).reshape(1, 64)).astype(int).ravel()
    flip = flip_horizontal(np.arange(64).reshape(1, 64)).astype(int).ravel()
    if experiment_id.startswith(("PL-", "AR-")):
        a = asymmetry(images, rot)
        b = asymmetry(images, flip)
        if a.shape != (24, 64) or sum_asymmetry(images, rot).shape != (24, 128):
            raise RuntimeError("Nieprawidłowy wymiar cech permutacyjnych")
        return {"asymmetry_shape": list(a.shape), "self_cka": linear_cka(a, a), "cross_cka": linear_cka(a, b)}
    if experiment_id.startswith("HD-"):
        x = rng.normal(size=(20, 63))
        perm = z3_permutation(63)
        if not np.array_equal(perm[perm[perm]], np.arange(63)):
            raise RuntimeError("Permutacja Z3 nie domyka się po trzech krokach")
        return {"feature_shape": list(z3_features(x, perm).shape), "order_three": True}
    provenance = json.loads((ROOT / "experiments" / "05_permutation_and_representation" / experiment_id / "provenance.json").read_text(encoding="utf-8"))
    result = ROOT / "experiments" / "05_permutation_and_representation" / experiment_id / "historical" / provenance["reported_result_file"]
    return {"reported_result_present": result.is_file(), "source_code_level": provenance["source_code_level"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=IDS, required=True)
    args = parser.parse_args()
    print(json.dumps({"experiment_id": args.only, "probe": probe(args.only)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
