#!/usr/bin/env python3
"""Szybka sonda strukturalna Etapu 11 bez pobierania MNIST."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bohn_original.adaptation_continual import (  # noqa: E402
    FewShotSBOHN, PermHeadSBOHN, parameter_count, parameter_count_of, select_trainable
)


def train_step(model, parameters) -> float:
    selected = select_trainable(model, parameters)
    optimizer = torch.optim.Adam(selected, lr=0.001)
    images = torch.rand(20, 1, 28, 28)
    labels = torch.arange(20) % 10
    optimizer.zero_grad(set_to_none=True)
    loss = F.cross_entropy(model(images), labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def probe_small() -> dict:
    torch.manual_seed(42)
    model = PermHeadSBOHN()
    before = model.save_task_params()
    loss = train_step(model, model.adaptation_params())
    changed = model.save_task_params()
    model.load_task_params(before)
    restored = model.save_task_params()
    exact = all(torch.equal(a, b) for a, b in zip(before["perm"], restored["perm"]))
    exact = exact and torch.equal(before["head_w"], restored["head_w"])
    exact = exact and torch.equal(before["head_b"], restored["head_b"])
    moved = any(not torch.equal(a, b) for a, b in zip(before["perm"], changed["perm"]))
    return {
        "model_parameters": parameter_count(model),
        "task_parameters": parameter_count_of(model.adaptation_params()),
        "loss": loss, "adaptation_changed": moved, "task_restore_exact": exact,
    }


def probe_large() -> dict:
    torch.manual_seed(42)
    model = FewShotSBOHN()
    before = model.save_permutations()
    loss = train_step(model, model.perm_only_params())
    model.load_permutations(before)
    after = model.save_permutations()
    return {
        "model_parameters": parameter_count(model),
        "perm_parameters": parameter_count_of(model.perm_only_params()),
        "loss": loss,
        "permutation_restore_exact": all(torch.equal(a, b) for a, b in zip(before, after)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("AD-001", "AD-002", "AD-003", "CL-001", "CL-002"))
    args = parser.parse_args()
    group = "small" if args.only in {None, "AD-001", "CL-001"} else "large"
    payload = probe_small() if group == "small" else probe_large()
    if not all(value for key, value in payload.items() if key.endswith("exact") or key.endswith("changed")):
        raise SystemExit("Sonda strukturalna nie spełniła kontraktu")
    print(json.dumps({"probe": group, **payload}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
