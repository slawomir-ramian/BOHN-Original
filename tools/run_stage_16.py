#!/usr/bin/env python3
"""Orchestrate the two supplementary Stage 16 units and preserve results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNITS = ("SOTA-002R", "SOTA-002H")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(unit: str, raw: Path, smoke: bool, threads: int) -> tuple[dict, str, str, int]:
    target = raw / f"{unit}_result.json"
    command = [
        sys.executable, "-u", str(ROOT / "tools" / "run_stage_16_unit.py"),
        "--unit", unit, "--output", str(target), "--threads", str(threads),
    ]
    if smoke:
        command.append("--smoke")
    process = subprocess.Popen(
        command, cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    started = time.perf_counter()
    last_heartbeat = started
    while process.poll() is None:
        now = time.perf_counter()
        if now - last_heartbeat >= 60:
            print(f"{unit}: nadal dziala | {now-started:.0f} s", flush=True)
            last_heartbeat = now
        time.sleep(0.5)
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout.rstrip(), flush=True)
    if process.returncode != 0 or not target.exists():
        return {}, stdout, stderr, process.returncode or 1
    return json.loads(target.read_text(encoding="utf-8")), stdout, stderr, 0


def write_report(output: Path, results: dict, smoke: bool) -> None:
    direct = results["units"]["SOTA-002R"]
    hierarchical = results["units"]["SOTA-002H"]
    if results["status"] != "PASS":
        lines = [
            "# Etap 16 — raport SOTA-002R/SOTA-002H",
            "",
            f"Tryb: **{'SMOKE' if smoke else 'FULL'}**  ",
            "Wynik ogólny: **FAILED**",
            "",
            "Szczegóły błędu znajdują się w katalogu `raw/`. Nie sformułowano wniosku naukowego.",
            "",
        ]
        (output / "STAGE_16_REPORT_PL.md").write_text("\n".join(lines), encoding="utf-8")
        return
    direct_rows = direct["rows"]
    h_rows = hierarchical["rows"]
    lines = [
        "# Etap 16 — raport SOTA-002R/SOTA-002H",
        "",
        f"Tryb: **{'SMOKE' if smoke else 'FULL'}**  ",
        f"Wynik ogólny: **{results['status']}**",
        "",
        "## Granice interpretacji",
        "",
        "- SOTA-002R używa niezmienionych klas historycznych i nie koduje cudzych wyników jako celu.",
        "- Rozdzielczość `3840` w historycznym modelu oznacza obraz kwadratowy 3840×3840, a nie UHD 3840×2160.",
        "- Baseline to dokładnie trzywarstwowy CNN z listingu; nie jest nazywany ResNetem.",
        "- SOTA-002H potwierdza wyłącznie kontrakt strukturalny: stałe parametry i 16 tokenów.",
        "- Nie zgłaszamy stałego czasu całego pipeline'u ani przewagi jakości klasyfikacji.",
        "",
        "## SOTA-002R — bezpośredni benchmark",
        "",
        "| Rozmiar | SBOHN ms | CNN ms | CNN/SBOHN | Parametry SBOHN | Tokeny |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in direct_rows:
        lines.append(
            f"| {row['display_shape']} | {row['historical_ms']:.3f} | {row['cnn_ms']:.3f} | "
            f"{row['cnn_over_historical_speedup']:.2f}× | {row['historical_params']:,} | {row['historical_token_count']} |"
        )
    lines.extend([
        "",
        "## SOTA-002H — stałoparametrowy front-end",
        "",
        "| Rozmiar | Czas ms | Parametry | Tokeny | Megapiksele |",
        "|---:|---:|---:|---:|---:|",
    ])
    for row in h_rows:
        lines.append(
            f"| {row['display_shape']} | {row['hierarchical_ms']:.3f} | {row['parameters']:,} | "
            f"{row['token_count']} | {row['input_megapixels']:.3f} |"
        )
    lines.extend([
        "",
        "## Wniosek techniczny",
        "",
        "Historyczny wariant zachowuje 16 tokenów, lecz jego gęsty embedder rośnie z rozdzielczością. "
        "Nowy wariant H usuwa wzrost liczby parametrów, ale nadal musi odczytać i skompresować wszystkie piksele; "
        "zatem jego koszt front-endu nie jest O(1).",
        "",
    ])
    (output / "STAGE_16_REPORT_PL.md").write_text("\n".join(lines), encoding="utf-8")


def write_manifest(output: Path) -> None:
    target = output / "MANIFEST_SHA256.txt"
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != target:
            rows.append(f"{sha256(path)}  {path.relative_to(output).as_posix()}")
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")


def update_inventory(result_path: str) -> None:
    path = ROOT / "inventory" / "supplementary_experiments.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    statuses = {"SOTA-002R": "DIRECT_REPLICATION_PASS", "SOTA-002H": "STRUCTURAL_FRONTEND_PASS"}
    for row in rows:
        if row["id"] in statuses:
            row["reproduction_status"] = statuses[row["id"]]
            row["result_path"] = result_path
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def archive(output: Path) -> Path:
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    target = artifacts / f"BOHN_ORIGINAL_STAGE_16_RESULTS_{output.name}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                handle.write(path, path.relative_to(output.parent))
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "reproduced" / "stage_16_runs" / timestamp
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=False)
    results = {
        "stage": 16,
        "mode": "SMOKE" if args.smoke else "FULL",
        "created_utc": timestamp,
        "python": sys.version,
        "platform": platform.platform(),
        "threads": args.threads,
        "units": {},
    }
    failed = False
    for unit in UNITS:
        print(f"RUN {unit} ...", flush=True)
        payload, stdout, stderr, code = execute(unit, raw, args.smoke, args.threads)
        (raw / f"{unit}_stdout.txt").write_text(stdout, encoding="utf-8")
        (raw / f"{unit}_stderr.txt").write_text(stderr, encoding="utf-8")
        if code:
            failed = True
            results["units"][unit] = {"status": "EXECUTION_FAILED", "return_code": code}
        else:
            results["units"][unit] = payload
    results["status"] = "PASS" if not failed else "FAILED"
    (output / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(output, results, args.smoke)
    write_manifest(output)
    latest = output.parent / "LATEST_RUN.txt"
    latest.write_text(output.name + "\n", encoding="utf-8")
    print(f"RESULTS: {output}")
    if not args.smoke and not failed:
        relative = output.relative_to(ROOT).as_posix()
        update_inventory(relative)
        target = archive(output)
        print(f"ZIP: {target}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
