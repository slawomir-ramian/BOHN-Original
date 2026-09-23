#!/usr/bin/env python3
"""Uruchom historyczne listingi SBOHN w kolejności ich wystąpienia w PDF-ie."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments" / "03_sbohn"

# Nie sortować numerycznie. To jest oryginalna chronologia PDF/LaTeX.
SOURCE_CHRONOLOGY = [
    "S-001", "S-002", "S-003", "S-004", "S-005", "S-006",
    "S-010", "S-011", "S-007", "S-008", "S-009",
]

AUDIT_NOTES = {
    "S-001": "Listing nie ustawia seedu NumPy; pojedynczy wynik nie jest deterministyczny.",
    "S-002": "Historyczny blok wyniku zawiera statystyki, których listing sam nie drukuje.",
    "S-003": "Historyczny blok wyniku zawiera statystyki, których listing sam nie drukuje.",
    "S-004": "W historycznym listingu licznik 'worse' omyłkowo używa warunku gains > 0; kod zachowano bez zmian.",
    "S-010": "Jednostka jest klasą referencyjną bez głównego przebiegu; sprawdzany jest kontrakt 64 -> 192.",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_lines(text: str) -> list[str]:
    return [
        " ".join(line.strip().split())
        for line in text.splitlines()
        if line.strip() and set(line.strip()) != {"="}
    ]


NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+\.\d+|\d+)(?![A-Za-z])")


def numeric_skeleton(line: str) -> tuple[str, list[float]]:
    values = [float(value) for value in NUMBER_RE.findall(line)]
    return NUMBER_RE.sub("<NUM>", line), values


def compare_text(actual: str, reported_path: Path) -> dict:
    if not reported_path.exists():
        return {"status": "NO_SEPARATE_REPORTED_OUTPUT"}
    reported = reported_path.read_text(encoding="utf-8")
    actual_lines = normalized_lines(actual)
    reported_lines = normalized_lines(reported)
    actual_set = set(actual_lines)
    reported_set = set(reported_lines)
    max_numeric_delta = None
    if actual_lines == reported_lines:
        status = "EXACT_TEXT_MATCH"
    elif actual_set <= reported_set:
        status = "REPORTED_SUPERSET_MATCH"
    else:
        status = "TEXT_OR_NUMERIC_DIFFERENCE"
        if len(actual_lines) == len(reported_lines):
            actual_parsed = [numeric_skeleton(line) for line in actual_lines]
            reported_parsed = [numeric_skeleton(line) for line in reported_lines]
            if [item[0] for item in actual_parsed] == [item[0] for item in reported_parsed]:
                deltas = []
                compatible = True
                for (_, actual_values), (_, reported_values) in zip(actual_parsed, reported_parsed, strict=True):
                    if len(actual_values) != len(reported_values):
                        compatible = False
                        break
                    deltas.extend(abs(a - b) for a, b in zip(actual_values, reported_values, strict=True))
                if compatible:
                    max_numeric_delta = max(deltas, default=0.0)
                    if max_numeric_delta <= 0.001:
                        status = "CLOSE_NUMERIC_MATCH"
    return {
        "status": status,
        "actual_line_count": len(actual_lines),
        "reported_line_count": len(reported_lines),
        "matching_actual_lines": sum(line in reported_set for line in actual_lines),
        "max_numeric_delta": max_numeric_delta,
    }


def run_historical(experiment_id: str, raw_dir: Path) -> dict:
    source = BASE / experiment_id / "historical" / "source_from_monograph.py"
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(source)],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=1800,
        check=False,
    )
    duration = time.perf_counter() - started
    stdout_path = raw_dir / f"{experiment_id}_stdout.txt"
    stderr_path = raw_dir / f"{experiment_id}_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
    comparison = compare_text(
        completed.stdout,
        BASE / experiment_id / "historical" / "reported_results.txt",
    )
    return {
        "execution_status": "PASS" if completed.returncode == 0 else "FAILED",
        "return_code": completed.returncode,
        "duration_seconds": round(duration, 6),
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "stdout_file": str(stdout_path.relative_to(raw_dir.parent)).replace("\\", "/"),
        "stderr_file": str(stderr_path.relative_to(raw_dir.parent)).replace("\\", "/"),
        "preliminary_comparison": comparison,
        "audit_note": AUDIT_NOTES.get(experiment_id),
    }


def run_s010_contract(raw_dir: Path) -> dict:
    experiment_id = "S-010"
    source = BASE / experiment_id / "historical" / "source_from_monograph.py"
    started = time.perf_counter()
    spec = importlib.util.spec_from_file_location("sbohn_s010_historical", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("Nie można załadować S-010")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import numpy as np

    extractor = module.SBOHNFeatureExtractor()
    X = np.random.default_rng(42).normal(size=(12, 64))
    phi = extractor.transform(X)
    order_three = bool(np.array_equal(extractor.perm_g2[extractor.perm_g], np.arange(64)))
    wrong_dimension_rejected = False
    try:
        extractor.transform(np.zeros((2, 63)))
    except ValueError:
        wrong_dimension_rejected = True
    passed = phi.shape == (12, 192) and order_three and wrong_dimension_rejected
    text = (
        "SBOHNFeatureExtractor contract\n"
        f"input_shape={X.shape}\n"
        f"output_shape={phi.shape}\n"
        f"z3_order_three={order_three}\n"
        f"wrong_dimension_rejected={wrong_dimension_rejected}\n"
    )
    stdout_path = raw_dir / "S-010_stdout.txt"
    stderr_path = raw_dir / "S-010_stderr.txt"
    stdout_path.write_text(text, encoding="utf-8", newline="\n")
    stderr_path.write_text("", encoding="utf-8", newline="\n")
    return {
        "execution_status": "PASS" if passed else "FAILED",
        "return_code": 0 if passed else 1,
        "duration_seconds": round(time.perf_counter() - started, 6),
        "stdout_sha256": sha256_bytes(text.encode("utf-8")),
        "stderr_sha256": sha256_bytes(b""),
        "stdout_file": "raw/S-010_stdout.txt",
        "stderr_file": "raw/S-010_stderr.txt",
        "preliminary_comparison": {"status": "CONTRACT_PASS" if passed else "CONTRACT_FAILED"},
        "audit_note": AUDIT_NOTES[experiment_id],
    }


def write_manifest(output_dir: Path) -> Path:
    manifest = output_dir / "MANIFEST_SHA256.txt"
    lines = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path != manifest:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            relative = str(path.relative_to(output_dir)).replace("\\", "/")
            lines.append(f"{digest}  {relative}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return manifest


def make_report(payload: dict) -> str:
    lines = [
        "# Etap 04 - raport wykonania SBOHN",
        "",
        "Jednostki wykonano w oryginalnej kolejności PDF-a, nie według sortowania ID.",
        "",
        "| Kolejność | ID | Wykonanie | Porównanie wstępne | Czas [s] |",
        "|---:|---|---|---|---:|",
    ]
    for position, experiment_id in enumerate(payload["source_chronology"], 1):
        result = payload["experiments"][experiment_id]
        comparison = result["preliminary_comparison"]["status"]
        lines.append(
            f"| {position} | {experiment_id} | {result['execution_status']} | "
            f"{comparison} | {result['duration_seconds']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Ważne",
            "",
            "Porównanie wstępne dotyczy tekstu drukowanego przez listing. Ostateczny status",
            "naukowy zostanie ustalony po analizie pełnego ZIP-a. Różnica tekstowa nie jest",
            "automatycznie różnicą merytoryczną.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--only", choices=SOURCE_CHRONOLOGY)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.only:
        selected = [args.only]
        mode = "only"
    elif args.smoke:
        selected = ["S-003", "S-010"]
        mode = "smoke"
    else:
        selected = SOURCE_CHRONOLOGY
        mode = "full"

    run_time = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or (ROOT / "reproduced" / "stage_04_runs" / stamp)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        if experiment_id == "S-010":
            result = run_s010_contract(raw_dir)
        else:
            result = run_historical(experiment_id, raw_dir)
        results[experiment_id] = result
        print(
            f"{experiment_id}: {result['execution_status']} | "
            f"{result['preliminary_comparison']['status']} | "
            f"{result['duration_seconds']:.2f} s",
            flush=True,
        )

    try:
        import numpy
        import sklearn
        numpy_version = numpy.__version__
        sklearn_version = sklearn.__version__
    except ImportError:
        numpy_version = None
        sklearn_version = None
    payload = {
        "stage": "04",
        "run_utc": run_time.isoformat(),
        "mode": mode,
        "source_chronology": selected,
        "full_source_chronology": SOURCE_CHRONOLOGY,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": numpy_version,
            "scikit_learn": sklearn_version,
            "processor_count": os.cpu_count(),
        },
        "experiments": results,
    }
    (output_dir / "results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (output_dir / "REPRODUCTION_REPORT_PL.md").write_text(
        make_report(payload), encoding="utf-8", newline="\n"
    )
    latest = ROOT / "reproduced" / "stage_04_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output_dir.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    write_manifest(output_dir)

    zip_path = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        base = artifacts / f"BOHN_ORIGINAL_STAGE_04_RESULTS_{stamp}"
        zip_path = Path(shutil.make_archive(str(base), "zip", root_dir=output_dir))
    print(f"RESULTS: {output_dir}")
    if zip_path:
        print(f"ZIP: {zip_path}")
    failed = any(result["execution_status"] == "FAILED" for result in results.values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
