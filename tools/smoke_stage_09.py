#!/usr/bin/env python3
"""Szybkie sondy Etapu 09; bez pobierania zbiorów danych."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
IDS = ["FR-001", "FR-002", "FR-003", "PT-001", "PT-003", "PT-004", "HR-003"]
AUDIT_IDS = {"FR-001", "PT-003", "HR-003"}


def probe(experiment_id: str) -> dict:
    from bohn_original.fractal_patch import (
        doubly_stochastic_error,
        extract_patches,
        log_sinkhorn,
        multiscale_features,
        permute_patch_sequence,
    )

    if experiment_id in AUDIT_IDS:
        provenance = json.loads(
            (ROOT / "experiments" / "07_fractal_patch" / experiment_id / "provenance.json").read_text(encoding="utf-8")
        )
        return {
            "audit_boundary_preserved": provenance["listing_target_code_present"] is False,
            "execution_mode": provenance["execution_mode"],
        }

    torch.manual_seed(42)
    images = torch.randn(4, 1, 32, 32)
    scores = torch.randn(4, 16, 16) * 0.2
    matrix = log_sinkhorn(scores, n_iter=20, tau=0.3)
    patches = extract_patches(images, patch_size=8)
    permuted = permute_patch_sequence(patches, matrix)
    levels = multiscale_features(images, levels=4)
    return {
        "finite": bool(torch.isfinite(matrix).all() and torch.isfinite(permuted).all()),
        "doubly_stochastic_error": doubly_stochastic_error(matrix),
        "patch_shape": list(patches.shape),
        "level_dims": [value.shape[1] for value in levels],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=IDS)
    args = parser.parse_args()
    selected = [args.only] if args.only else IDS
    for experiment_id in selected:
        result = probe(experiment_id)
        if result.get("finite", True) is not True or result.get("doubly_stochastic_error", 0.0) > 0.02:
            raise RuntimeError(f"Sonda {experiment_id} nie przeszła")
        if result.get("audit_boundary_preserved", True) is not True:
            raise RuntimeError(f"Granica źródła {experiment_id} nie jest zachowana")
        print(f"{experiment_id}: SMOKE_PROBE_PASS | {json.dumps(result, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
