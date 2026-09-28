#!/usr/bin/env python3
"""Szybkie sondy strukturalne Etapu 14."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.moe_evolution import ConfidenceRoutedMoE, HardAssignMoE, HybridBNLNMoE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", required=True)
    args = parser.parse_args()
    torch.manual_seed(14)
    base = ROOT / "experiments" / "12_moe_evolution" / args.only
    provenance = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
    if provenance["listing_target_code_present"] is False:
        source = base / "historical" / provenance["historical_source_files"][0]
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
        print(f"{args.only}: source-boundary audit probe PASS")
        return 0

    x = torch.randn(4, 1, 28, 28)
    if args.only == "MOE-004":
        model = HardAssignMoE()
        hard = model.forward_hard(x, 0)
        gated, logits, weights = model.forward_gated(x)
        assert hard.shape == gated.shape == (4, 10) and logits.shape == weights.shape == (4, 4)
    elif args.only == "MOE-006":
        model = ConfidenceRoutedMoE()
        output, selected = model.forward_confidence(x)
        assert output.shape == (4, 10) and selected.shape == (4,)
    elif args.only == "MOE-008":
        model = HybridBNLNMoE()
        output, logits, weights = model.forward_gated(x)
        assert output.shape == (4, 10) and logits.shape == weights.shape == (4, 4)
    else:
        raise SystemExit(f"Brak sondy dla {args.only}")
    print(f"{args.only}: architecture smoke probe PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
