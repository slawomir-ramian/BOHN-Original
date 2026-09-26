#!/usr/bin/env python3
"""Szybkie sondy Etapu 08; nie zastępują programów historycznych."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
IDS = ["LS-001", "LS-002", "LD-001", "LD-002", "LD-004", "LD-005"]


def probe(experiment_id: str) -> dict:
    from bohn_original.learnable_sinkhorn import (
        doubly_stochastic_error,
        log_sinkhorn,
        naive_sinkhorn,
        row_entropy,
    )

    torch.manual_seed(42)
    scores = torch.randn(8, 8) * 0.4
    if experiment_id == "LS-002":
        provenance = json.loads(
            (ROOT / "experiments" / "06_learnable_sinkhorn" / experiment_id / "provenance.json").read_text(encoding="utf-8")
        )
        ok = provenance["listing_target_code_present"] is False
        return {"audit_boundary_preserved": ok}
    if experiment_id in {"LS-001", "LD-001"}:
        matrix = naive_sinkhorn(scores, n_iters=20, tau=0.5)
    else:
        matrix = log_sinkhorn(scores, n_iters=20, tau=0.1)
    return {
        "finite": bool(torch.isfinite(matrix).all()),
        "doubly_stochastic_error": doubly_stochastic_error(matrix),
        "entropy": float(row_entropy(matrix)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=IDS)
    args = parser.parse_args()
    selected = [args.only] if args.only else IDS
    for experiment_id in selected:
        result = probe(experiment_id)
        if result.get("finite", True) is not True or result.get("doubly_stochastic_error", 0.0) > 0.02:
            raise RuntimeError(f"Sonda {experiment_id} nie przeszla")
        if result.get("audit_boundary_preserved", True) is not True:
            raise RuntimeError(f"Granica zrodla {experiment_id} nie jest zachowana")
        print(f"{experiment_id}: SMOKE_PROBE_PASS | {json.dumps(result, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
