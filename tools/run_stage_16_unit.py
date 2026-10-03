#!/usr/bin/env python3
"""Execute one frozen Stage 16 supplementary benchmark unit."""
from __future__ import annotations

import argparse
import gc
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch

from bohn_original.sota_scaling import CNN, FractalSBOHN, parameter_count
from bohn_original.stage16_high_resolution import HierarchicalFractalSBOHN

PROTOCOL_PATH = ROOT / "experiments" / "14_sota002_high_resolution_supplementary" / "stage16_protocol.json"


def median_ms(function, warmups: int, repeats: int) -> float:
    with torch.inference_mode():
        for _ in range(warmups):
            function()
        samples = []
        for _ in range(repeats):
            started = time.perf_counter_ns()
            function()
            samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return statistics.median(samples)


def finite_output(model, tensor: torch.Tensor) -> bool:
    with torch.inference_mode():
        output = model(tensor)
    return bool(torch.isfinite(output).all().item()) and tuple(output.shape) == (1, 10)


def historical_core(model: FractalSBOHN, hidden: torch.Tensor) -> torch.Tensor:
    batch = hidden.shape[0]
    for layer, pool in zip(model.lvs, model.pls):
        hidden = pool(layer(hidden).reshape(batch, -1)).view(batch, -1, model.fd)
    return model.cls(hidden.reshape(batch, -1))


def profile_historical(model: FractalSBOHN, x: torch.Tensor, warmups: int, repeats: int) -> dict:
    batch = x.shape[0]

    def extract():
        return x.unfold(2, model.ps, model.ps).unfold(3, model.ps, model.ps).permute(
            0, 2, 3, 1, 4, 5
        ).contiguous().view(batch, model.np, -1)

    with torch.inference_mode():
        patches = extract()
        first = model.pe[0](patches)
        tokens = model.pe(patches)
    return {
        "patch_extract_ms": median_ms(extract, warmups, repeats),
        "first_dense_layer_ms": median_ms(lambda: model.pe[0](patches), warmups, repeats),
        "complete_embedder_ms": median_ms(lambda: model.pe(patches), warmups, repeats),
        "relational_core_and_head_ms": median_ms(lambda: historical_core(model, tokens), warmups, repeats),
        "first_dense_output_shape": list(first.shape),
    }


def profile_hierarchical(model: HierarchicalFractalSBOHN, x: torch.Tensor, warmups: int, repeats: int) -> dict:
    with torch.inference_mode():
        tokens = model.encode_tokens(x)
    return {
        "front_end_ms": median_ms(lambda: model.encode_tokens(x), warmups, repeats),
        "relational_core_and_head_ms": median_ms(lambda: model.relational_core(tokens), warmups, repeats),
        "token_shape": list(tokens.shape),
    }


def run_direct(protocol: dict, smoke: bool, warmups: int, repeats: int) -> dict:
    resolutions = protocol["square_resolutions"][:3] if smoke else protocol["square_resolutions"]
    rows = []
    highest_model = None
    highest_input = None
    for resolution in resolutions:
        torch.manual_seed(16000 + resolution)
        x = torch.randn(1, 1, resolution, resolution, dtype=torch.float32)
        historical = FractalSBOHN(resolution, 1, 10, 16, 4).eval()
        baseline = CNN(1, 10).eval()
        historical_ms = median_ms(lambda: historical(x), warmups, repeats)
        baseline_ms = median_ms(lambda: baseline(x), warmups, repeats)
        row = {
            "shape_hw": [resolution, resolution],
            "display_shape": f"{resolution}x{resolution}",
            "historical_ms": historical_ms,
            "cnn_ms": baseline_ms,
            "cnn_over_historical_speedup": baseline_ms / historical_ms,
            "historical_params": parameter_count(historical),
            "cnn_params": parameter_count(baseline),
            "historical_patch_side": historical.ps,
            "historical_token_count": historical.np,
            "historical_output_finite": finite_output(historical, x),
            "cnn_output_finite": finite_output(baseline, x),
        }
        rows.append(row)
        if resolution == resolutions[-1]:
            highest_model, highest_input = historical, x
        del baseline
        gc.collect()

    profile = profile_historical(highest_model, highest_input, warmups, repeats)
    parameter_counts = [row["historical_params"] for row in rows]
    all_valid = all(row["historical_output_finite"] and row["cnn_output_finite"] for row in rows)
    return {
        "unit": "SOTA-002R",
        "mode": "SMOKE" if smoke else "FULL",
        "status": "DIRECT_REPLICATION_PASS" if all_valid else "DIRECT_REPLICATION_FAILED",
        "scientific_target_hardcoded": False,
        "historical_source_modified": False,
        "square_3840_semantics": "3840x3840, not 3840x2160 UHD",
        "baseline_description": "three-convolution CNN from the historical listing",
        "rows": rows,
        "highest_resolution_profile": profile,
        "parameter_growth_factor": max(parameter_counts) / min(parameter_counts),
    }


def run_hierarchical(protocol: dict, smoke: bool, warmups: int, repeats: int) -> dict:
    square = protocol["square_resolutions"][:3] if smoke else protocol["square_resolutions"]
    rectangular = [] if smoke else protocol["rectangular_resolutions_hw"]
    shapes = [(side, side) for side in square] + [tuple(pair) for pair in rectangular]
    torch.manual_seed(16002)
    model = HierarchicalFractalSBOHN(ch=1, nc=10, fd=16, nh=4).eval()
    fixed_parameters = parameter_count(model)
    rows = []
    profile_input = None
    for height, width in shapes:
        torch.manual_seed(17000 + height + width)
        x = torch.randn(1, 1, height, width, dtype=torch.float32)
        elapsed = median_ms(lambda: model(x), warmups, repeats)
        with torch.inference_mode():
            tokens = model.encode_tokens(x)
            output = model.relational_core(tokens)
        rows.append({
            "shape_hw": [height, width],
            "display_shape": f"{width}x{height}",
            "hierarchical_ms": elapsed,
            "parameters": fixed_parameters,
            "token_count": int(tokens.shape[1]),
            "output_finite": bool(torch.isfinite(output).all().item()),
            "input_megapixels": height * width / 1_000_000.0,
        })
        if (height, width) == ((2160, 3840) if not smoke else shapes[-1]):
            profile_input = x
        else:
            del x
        gc.collect()

    profile = profile_hierarchical(model, profile_input, warmups, repeats)
    parameter_values = {row["parameters"] for row in rows}
    tokens = {row["token_count"] for row in rows}
    passed = len(parameter_values) == 1 and tokens == {16} and all(row["output_finite"] for row in rows)
    return {
        "unit": "SOTA-002H",
        "mode": "SMOKE" if smoke else "FULL",
        "status": "STRUCTURAL_FRONTEND_PASS" if passed else "STRUCTURAL_FRONTEND_FAILED",
        "architecture_claim_only": True,
        "classification_accuracy_claim": False,
        "entire_pipeline_o1_claim": False,
        "model_reused_across_all_resolutions": True,
        "rows": rows,
        "uhd_profile": profile,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=("SOTA-002R", "SOTA-002H"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--threads", type=int, default=None)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    threads = args.threads or int(protocol["threads"])
    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    warmups = int(protocol["smoke_warmups"] if args.smoke else protocol["full_warmups"])
    repeats = int(protocol["smoke_repeats"] if args.smoke else protocol["full_repeats"])
    started = time.perf_counter()
    result = run_direct(protocol, args.smoke, warmups, repeats) if args.unit == "SOTA-002R" else run_hierarchical(protocol, args.smoke, warmups, repeats)
    result.update({
        "duration_seconds": time.perf_counter() - started,
        "threads": threads,
        "torch_version": torch.__version__,
        "dtype": "float32",
        "batch_size": 1,
        "warmups": warmups,
        "repeats": repeats,
        "timer": "time.perf_counter_ns median",
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.unit}: {result['status']} | {result['duration_seconds']:.2f} s")
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

