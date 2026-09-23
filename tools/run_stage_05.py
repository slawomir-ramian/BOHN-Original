#!/usr/bin/env python3
"""Uruchom Etap 05 w kolejności wystąpienia jednostek w PDF-ie."""

from __future__ import annotations

import argparse
import hashlib
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
BASE = ROOT / "experiments" / "04_generalization_so2"
SOURCE_CHRONOLOGY = [
    "G-001", "SO-001", "SO-002", "SO-003",
    "SO-004", "SO-005", "SO-006", "SO-007",
]
EXECUTION_MODE = {
    "G-001": "HISTORICAL_SOURCE",
    "SO-001": "RECONSTRUCTION_OF_SILENT_SOURCE",
    "SO-002": "RECONSTRUCTION_FROM_FORMULA",
    "SO-003": "RECONSTRUCTION_FROM_FORMULA",
    "SO-004": "RECONSTRUCTION_FROM_FORMULA",
    "SO-005": "RECONSTRUCTION_FROM_SHARED_FRAGMENT",
    "SO-006": "RECONSTRUCTION_FROM_SHARED_FRAGMENT",
    "SO-007": "RECONSTRUCTION_FROM_SHARED_FRAGMENT",
}
AUDIT_NOTES = {
    "G-001": "Pełny kod historyczny wykonany bez zmian.",
    "SO-001": "Listing oblicza symetryzator, ale nie zawiera print; odtworzono wyłącznie raportowanie.",
    "SO-002": "Brak listingu kodu; rekonstrukcja z opublikowanego wzoru A_x(theta).",
    "SO-003": "Brak listingu kodu; rekonstrukcja z opublikowanego wzoru momentów z funkcją Beta.",
    "SO-004": "Brak listingu kodu; rekonstrukcja z opublikowanej definicji współczynników Fouriera.",
    "SO-005": "Monografia publikuje ekstraktor cech, lecz nie pełny generator danych i protokół.",
    "SO-006": "Monografia publikuje ekstraktor cech, lecz nie pełny generator danych i protokół.",
    "SO-007": "Test odtworzony z opublikowanego fragmentu ekstraktora i definicji inwariantności.",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_lines(text: str) -> list[str]:
    return [
        " ".join(line.strip().split())
        for line in text.splitlines()
        if line.strip() and len(set(line.strip())) > 1
    ]


NUMBER_RE = re.compile(
    r"(?<![A-Za-z])[-+]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)(?![A-Za-z])"
)


def numeric_skeleton(line: str) -> tuple[str, list[float]]:
    values = [float(value) for value in NUMBER_RE.findall(line)]
    return NUMBER_RE.sub("<NUM>", line), values


def compare_text(actual: str, reported_path: Path) -> dict:
    reported = reported_path.read_text(encoding="utf-8")
    actual_lines = normalized_lines(actual)
    reported_lines = normalized_lines(reported)
    status = "TEXT_OR_NUMERIC_DIFFERENCE"
    max_numeric_delta = None
    skeleton_match = False
    if actual_lines == reported_lines:
        status = "EXACT_TEXT_MATCH"
    elif len(actual_lines) == len(reported_lines):
        actual_parsed = [numeric_skeleton(line) for line in actual_lines]
        reported_parsed = [numeric_skeleton(line) for line in reported_lines]
        skeleton_match = [item[0] for item in actual_parsed] == [item[0] for item in reported_parsed]
        if skeleton_match:
            deltas = []
            compatible = True
            for (_, actual_values), (_, reported_values) in zip(actual_parsed, reported_parsed, strict=True):
                if len(actual_values) != len(reported_values):
                    compatible = False
                    break
                deltas.extend(
                    abs(a - b)
                    for a, b in zip(actual_values, reported_values, strict=True)
                )
            if compatible:
                max_numeric_delta = max(deltas, default=0.0)
                status = "CLOSE_NUMERIC_MATCH" if max_numeric_delta <= 0.001 else "NUMERIC_DIFFERENCE"
    return {
        "status": status,
        "actual_line_count": len(actual_lines),
        "reported_line_count": len(reported_lines),
        "matching_skeleton": skeleton_match,
        "max_numeric_delta": max_numeric_delta,
    }


def execution_path(experiment_id: str) -> Path:
    if experiment_id == "G-001":
        return BASE / experiment_id / "historical" / "source_from_monograph.py"
    return BASE / experiment_id / "reconstruction" / "reproduce.py"


def run_unit(experiment_id: str, raw_dir: Path) -> dict:
    source = execution_path(experiment_id)
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
        completed.stdout, BASE / experiment_id / "historical" / "reported_results.txt"
    )
    return {
        "execution_status": "PASS" if completed.returncode == 0 else "FAILED",
        "return_code": completed.returncode,
        "duration_seconds": round(duration, 6),
        "execution_mode": EXECUTION_MODE[experiment_id],
        "executed_file": str(source.relative_to(ROOT)).replace("\\", "/"),
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "stdout_file": str(stdout_path.relative_to(raw_dir.parent)).replace("\\", "/"),
        "stderr_file": str(stderr_path.relative_to(raw_dir.parent)).replace("\\", "/"),
        "preliminary_comparison": comparison,
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
        "# Etap 05 - raport wykonania uogólnienia SO(2)",
        "",
        "Jednostki wykonano w oryginalnej kolejności PDF-a.",
        "",
        "| Kolejność | ID | Tryb | Wykonanie | Porównanie wstępne | Czas [s] |",
        "|---:|---|---|---|---|---:|",
    ]
    for position, experiment_id in enumerate(payload["source_chronology"], 1):
        result = payload["experiments"][experiment_id]
        lines.append(
            f"| {position} | {experiment_id} | {result['execution_mode']} | "
            f"{result['execution_status']} | "
            f"{result['preliminary_comparison']['status']} | "
            f"{result['duration_seconds']:.3f} |"
        )
    lines.extend([
        "",
        "## Ważne",
        "",
        "Tylko `G-001` jest bezpośrednim wykonaniem pełnego historycznego programu.",
        "Pozostałe jednostki jawnie odtwarzają brakujące raportowanie lub protokół",
        "z opublikowanych wzorów, fragmentów i opisów. Zgodność jakościowa nie",
        "jest automatycznie ścisłą reprodukcją liczbową.",
    ])
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
        selected = ["G-001", "SO-001", "SO-007"]
        mode = "smoke"
    else:
        selected = SOURCE_CHRONOLOGY
        mode = "full"

    run_time = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or (ROOT / "reproduced" / "stage_05_runs" / stamp)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        result = run_unit(experiment_id, raw_dir)
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
        "stage": "05",
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
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    (output_dir / "REPRODUCTION_REPORT_PL.md").write_text(
        make_report(payload), encoding="utf-8", newline="\n"
    )
    latest = ROOT / "reproduced" / "stage_05_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    try:
        latest_value = str(output_dir.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        latest_value = str(output_dir)
    latest.write_text(
        latest_value + "\n",
        encoding="utf-8", newline="\n",
    )
    write_manifest(output_dir)

    zip_path = None
    if mode == "full":
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        base = artifacts / f"BOHN_ORIGINAL_STAGE_05_RESULTS_{stamp}"
        zip_path = Path(shutil.make_archive(str(base), "zip", root_dir=output_dir))
    print(f"RESULTS: {output_dir}")
    if zip_path:
        print(f"ZIP: {zip_path}")
    failed = any(result["execution_status"] == "FAILED" for result in results.values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
