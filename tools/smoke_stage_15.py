#!/usr/bin/env python3
"""Szybkie sondy strukturalne Etapu 15."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.rmig_meta_fbohn import (OPS, check_z3_equivariance, fbohn_features,
                                           fbohn_poly_control_features, generate_signals,
                                           symbolic_op, weighted_fbohn_orbitwise, z3_permutation)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", required=True)
    args = parser.parse_args()
    base = ROOT / "experiments" / "13_rmig_meta_fbohn" / args.only
    provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["source_code_level"] == "FULL_SUITE"
    source = base / "historical" / provenance["historical_source_files"][0]
    compile(source.read_text(encoding="utf-8"), str(source), "exec")

    signals = generate_signals(32, seed=15)
    features = fbohn_features(signals)
    assert signals.shape == (32, 18) and features.shape == (32, 30)
    assert fbohn_poly_control_features(signals).shape == (32, 84)
    assert check_z3_equivariance()
    assert np.allclose(features, fbohn_features(signals[:, z3_permutation(1)]))
    weighted = weighted_fbohn_orbitwise(signals, np.linspace(-1, 1, 30))
    assert weighted.shape == features.shape and np.isfinite(weighted).all()
    for operator in OPS:
        assert np.isfinite(symbolic_op(features[:, 0], features[:, 1], operator)).all()
    print(f"{args.only}: structural smoke probe PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
