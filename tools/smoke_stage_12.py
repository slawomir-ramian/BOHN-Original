#!/usr/bin/env python3
"""Krótka sonda architektur Etapu 12 bez pobierania zbioru danych."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["SOTA-001", "SOTA-002"], required=True)
    args = parser.parse_args()
    import torch
    from bohn_original.sota_scaling import CNN, FractalSBOHN, MLP, ViT, parameter_count

    with torch.no_grad():
        models = {
            "Fractal_SBOHN_v2": FractalSBOHN(28, 1, 10, 16, 4),
            "CNN": CNN(1, 10),
            "ViT-Tiny": ViT(28, 1, 10, 64, 4, 2),
        }
        shapes = {name: list(model(torch.randn(1, 1, 28, 28)).shape) for name, model in models.items()}
        if args.only == "SOTA-001":
            models["MLP"] = MLP(784, 10)
            shapes["MLP"] = list(models["MLP"](torch.randn(1, 1, 28, 28)).shape)
        payload = {
            "id": args.only,
            "shapes": shapes,
            "params": {name: parameter_count(model) for name, model in models.items()},
        }
    print(json.dumps(payload, sort_keys=True))
    return 0 if all(shape == [1, 10] for shape in shapes.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
