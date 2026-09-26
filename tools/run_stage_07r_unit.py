#!/usr/bin/env python3
"""Uruchom pojedynczą jawną rekonstrukcję Etapu 07."""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from sklearn.exceptions import ConvergenceWarning

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bohn_original.stage07_supplementary import (  # noqa: E402
    run_cmp001r,
    run_cmp002r,
    run_hd003r,
    run_pl002r,
    run_pl003r,
)

BASE = ROOT / "experiments" / "05_permutation_and_representation_supplementary"
PROTOCOL = json.loads((BASE / "STAGE_07R_PROTOCOL.json").read_text(encoding="utf-8"))
IDS = ["PL-002R", "PL-003R", "HD-003R", "CMP-001R", "CMP-002R"]


def configuration(experiment_id: str, mode: str) -> dict:
    full = PROTOCOL["full"]
    pilot = PROTOCOL["pilot"]
    if experiment_id == "PL-002R":
        return {
            "label_seed": full["label_seed"],
            "split_seed": full["label_seed"],
            "evolution_seed": full["pl2_evolution_seed"] if mode == "full" else pilot["seed"],
            "population": full["pl2_population"] if mode == "full" else pilot["pl2_population"],
            "generations": full["pl2_generations"] if mode == "full" else pilot["pl2_generations"],
            "elite": full["pl2_elite"] if mode == "full" else 4,
            "mutation_swaps": full["pl2_mutation_swaps"],
        }
    if experiment_id == "PL-003R":
        return {"label_seed": full["label_seed"], "split_seed": full["label_seed"], "seed": full["pl3_seed"] if mode == "full" else pilot["seed"], "k_values": full["pl3_k_values"] if mode == "full" else pilot["pl3_k_values"]}
    if experiment_id == "HD-003R":
        return {"n": full["hd_n"] if mode == "full" else 600, "dimensions": full["hd_dimensions"] if mode == "full" else pilot["hd_dimensions"], "seeds": full["hd_seeds"] if mode == "full" else pilot["hd_seeds"], "noise_std": full["hd_noise_std"]}
    if experiment_id == "CMP-001R":
        return {"label_seed": full["label_seed"], "seed": full["cmp1_seed"] if mode == "full" else pilot["cmp_seeds"][0], "bottleneck": full["cmp1_bottleneck"], "autoencoder_hidden": full["cmp1_autoencoder_hidden"], "autoencoder_max_iter": full["cmp1_autoencoder_max_iter"] if mode == "full" else 50}
    return {"label_seed": full["label_seed"], "seeds": full["cmp2_seeds"] if mode == "full" else pilot["cmp_seeds"], "latent_dimensions": full["cmp2_latent_dimensions"], "hidden_width": full["cmp2_hidden_width"], "max_iter": full["cmp2_max_iter"] if mode == "full" else 100}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", choices=IDS, required=True)
    parser.add_argument("--mode", choices=["pilot", "full"], required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    functions = {"PL-002R": run_pl002r, "PL-003R": run_pl003r, "HD-003R": run_hd003r, "CMP-001R": run_cmp001r, "CMP-002R": run_cmp002r}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = functions[args.id](configuration(args.id, args.mode))
    result["mode"] = args.mode
    result["protocol_id"] = PROTOCOL["protocol_id"]
    result["warnings"] = [{"category": item.category.__name__, "message": str(item.message)} for item in caught]
    result["convergence_warning_count"] = sum(issubclass(item.category, ConvergenceWarning) for item in caught)
    if args.mode == "pilot":
        result["pilot_execution_pass"] = True
        result["status"] = "STRUCTURAL_PILOT_PASS"
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.id}: {result['status']}", flush=True)
    print("RESULT_JSON=" + json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
