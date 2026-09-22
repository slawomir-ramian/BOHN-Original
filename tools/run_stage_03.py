#!/usr/bin/env python3
"""Uruchom reprodukcję fundamentu BOHN B-001--B-009."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from bohn_original.foundation import (
    ReversibleRMIGLayer,
    compute_orbit_energies,
    compute_orbit_histogram,
    compute_z3_orbits,
    generate_linear_data,
    generate_z3_data_rich,
    generate_z3_symmetric_data,
    test_gradient_input,
    test_gradient_weights,
    test_invariance_batch,
    test_invariance_single,
    test_reversibility,
    z3_permutation,
)

IDS = [f"B-{number:03d}" for number in range(1, 10)]
REPORTED = {
    "B-005": {"linear": 0.962, "rmig_frozen": 0.741, "rmig_trainable": 0.940},
    "B-006": {
        "linear_raw": 0.483,
        "rmig_frozen": 0.471,
        "rmig_trainable_reported_constant": 0.470,
        "orbit_energy": 0.981,
    },
    "B-007": {"linear_raw": 0.483, "linear_orbit_energy": 0.982, "mlp_orbit_energy": 0.983},
    "B-008": {"linear_raw": 0.506, "linear_histogram": 0.968, "mlp_histogram": 0.984},
}


def _sklearn():
    try:
        import sklearn
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
        from sklearn.model_selection import train_test_split
        from sklearn.neural_network import MLPClassifier
    except ImportError as exc:
        raise SystemExit(
            "Brak scikit-learn. Uruchom najpierw SETUP_STAGE_03.ps1."
        ) from exc
    return sklearn, LogisticRegression, accuracy_score, train_test_split, MLPClassifier


def rounded_match(actual: dict, reported: dict) -> tuple[str, dict]:
    deltas = {key: round(float(actual[key]) - expected, 12) for key, expected in reported.items()}
    same = all(round(float(actual[key]), 3) == expected for key, expected in reported.items())
    close = all(abs(delta) <= 0.01 for delta in deltas.values())
    return ("EXACT_MATCH" if same else "CLOSE_MATCH" if close else "DIVERGENT"), deltas


def run_b001(orbits):
    singleton = [orbit for orbit in orbits if len(orbit) == 1]
    triple = [orbit for orbit in orbits if len(orbit) == 3]
    fix_g = sum(z3_permutation(state) == state for state in range(64))
    fix_g2 = sum(z3_permutation(z3_permutation(state)) == state for state in range(64))
    values = {
        "states": 64,
        "orbits": len(orbits),
        "singletons": len(singleton),
        "triples": len(triple),
        "fix_e": 64,
        "fix_g": fix_g,
        "fix_g2": fix_g2,
        "singleton_states": [orbit[0] for orbit in singleton],
    }
    expected = {
        "orbits": 24,
        "singletons": 4,
        "triples": 20,
        "fix_g": 4,
        "fix_g2": 4,
        "singleton_states": [0, 21, 42, 63],
    }
    return {"status": "EXACT_MATCH" if all(values[k] == v for k, v in expected.items()) else "DIVERGENT", "values": values}


def run_b002(orbits):
    np.random.seed(42)
    X = np.random.randn(64)
    phi = compute_orbit_histogram(X, orbits)
    return {
        "status": "VERIFIED_NO_REFERENCE_BLOCK" if phi.shape == (72,) else "DIVERGENT",
        "values": {
            "input_dimension": 64,
            "histogram_dimension": int(phi.shape[0]),
            "first_five_energy": phi[:5].tolist(),
            "first_five_mean": phi[24:29].tolist(),
            "first_five_amplitude": phi[48:53].tolist(),
        },
    }


def run_b003(orbits):
    layer = ReversibleRMIGLayer(seed=42)
    X = np.arange(64, dtype=float)
    exact = bool(np.array_equal(layer.inverse(layer.forward(X)), X))
    values = {
        "states": layer.n_states,
        "weight_shape": list(layer.weights.shape),
        "unique_weights": np.unique(layer.weights).tolist(),
        "perm_first_five": layer.perm[:5].tolist(),
        "exact_roundtrip": exact,
    }
    return {"status": "VERIFIED_NO_REFERENCE_BLOCK" if exact else "DIVERGENT", "values": values}


def run_b004(orbits):
    np.random.seed(42)
    layer = ReversibleRMIGLayer(seed=42)
    eps_rec = test_reversibility(layer)
    eps_x, grad_x_a, grad_x_n = test_gradient_input(layer)
    eps_w, grad_w_a, grad_w_n = test_gradient_weights(layer)
    passed = eps_rec == 0.0 and eps_x < 1e-6 and eps_w < 1e-6
    return {
        "status": "CLOSE_MATCH" if passed else "DIVERGENT",
        "note": "Zgodność kryteriów PASS; wartości zmiennoprzecinkowe zależą od środowiska.",
        "values": {
            "reversibility_error": float(eps_rec),
            "input_gradient_error": float(eps_x),
            "input_gradient_analytic_norm": float(np.linalg.norm(grad_x_a)),
            "input_gradient_numeric_norm": float(np.linalg.norm(grad_x_n)),
            "weight_gradient_error": float(eps_w),
            "weight_gradient_analytic_norm": float(np.linalg.norm(grad_w_a)),
            "weight_gradient_numeric_norm": float(np.linalg.norm(grad_w_n)),
            "all_tests_passed": bool(passed),
        },
    }


def run_b005(orbits):
    _, LogisticRegression, accuracy_score, train_test_split, _ = _sklearn()
    X, y = generate_linear_data(n_samples=2000, dim=64, seed=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    linear = LogisticRegression(max_iter=1000, random_state=42)
    linear.fit(X_train, y_train)
    acc_linear = accuracy_score(y_test, linear.predict(X_test))
    frozen = ReversibleRMIGLayer(seed=42)
    X_train_f = frozen.forward(X_train)
    X_test_f = frozen.forward(X_test)
    model_f = LogisticRegression(max_iter=1000, random_state=42)
    model_f.fit(X_train_f, y_train)
    acc_frozen = accuracy_score(y_test, model_f.predict(X_test_f))
    best_acc = 0.0
    best_weights = frozen.weights.copy()
    rng = np.random.RandomState(123)
    for _ in range(50):
        trial_weights = best_weights.copy()
        flip_idx = rng.choice(64, rng.randint(1, 10), replace=False)
        trial_weights[flip_idx] *= -1
        layer = ReversibleRMIGLayer(seed=42)
        layer.set_weights(trial_weights)
        model = LogisticRegression(max_iter=500, random_state=42)
        model.fit(layer.forward(X_train), y_train)
        acc = accuracy_score(y_test, model.predict(layer.forward(X_test)))
        if acc > best_acc:
            best_acc = acc
            best_weights = trial_weights.copy()
    values = {"linear": float(acc_linear), "rmig_frozen": float(acc_frozen), "rmig_trainable": float(best_acc)}
    status, deltas = rounded_match(values, REPORTED["B-005"])
    return {
        "status": status,
        "values": values,
        "reported": REPORTED["B-005"],
        "delta_reproduced_minus_reported": deltas,
        "audit_note": "Odwracalne przestawienie i zmiana znaków zachowują klasę modeli liniowych; listing daje identyczne predykcje dla trzech wariantów w tym środowisku.",
    }


def run_b006(orbits):
    _, LogisticRegression, accuracy_score, train_test_split, _ = _sklearn()
    X, y = generate_z3_symmetric_data(n_samples=2000, dim=64, orbits=orbits, seed=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model_raw = LogisticRegression(max_iter=1000, random_state=42)
    model_raw.fit(X_train, y_train)
    layer = ReversibleRMIGLayer(seed=42)
    model_rmig = LogisticRegression(max_iter=1000, random_state=42)
    model_rmig.fit(layer.forward(X_train), y_train)
    E_train = compute_orbit_energies(X_train, orbits)
    E_test = compute_orbit_energies(X_test, orbits)
    model_energy = LogisticRegression(max_iter=1000, random_state=42)
    model_energy.fit(E_train, y_train)
    values = {
        "linear_raw": float(accuracy_score(y_test, model_raw.predict(X_test))),
        "rmig_frozen": float(accuracy_score(y_test, model_rmig.predict(layer.forward(X_test)))),
        "rmig_trainable_reported_constant": 0.470,
        "orbit_energy": float(accuracy_score(y_test, model_energy.predict(E_test))),
    }
    _, deltas = rounded_match(values, REPORTED["B-006"])
    return {
        "status": "PARTIAL",
        "values": values,
        "reported": REPORTED["B-006"],
        "delta_reproduced_minus_reported": deltas,
        "audit_note": "W listingu wartość RMIG trainable = 0.470 jest wpisana na stałe i nie jest obliczana; dlatego reprodukcja pozostaje PARTIAL.",
    }


def run_b007(orbits):
    _, LogisticRegression, accuracy_score, train_test_split, MLPClassifier = _sklearn()
    X, y = generate_z3_symmetric_data(n_samples=2000, dim=64, orbits=orbits, seed=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    E_train = compute_orbit_energies(X_train, orbits)
    E_test = compute_orbit_energies(X_test, orbits)
    raw = LogisticRegression(max_iter=1000, random_state=42).fit(X_train, y_train)
    linear = LogisticRegression(max_iter=1000, random_state=42).fit(E_train, y_train)
    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42, early_stopping=True).fit(E_train, y_train)
    values = {
        "linear_raw": float(accuracy_score(y_test, raw.predict(X_test))),
        "linear_orbit_energy": float(accuracy_score(y_test, linear.predict(E_test))),
        "mlp_orbit_energy": float(accuracy_score(y_test, mlp.predict(E_test))),
    }
    status, deltas = rounded_match(values, REPORTED["B-007"])
    return {"status": status, "values": values, "reported": REPORTED["B-007"], "delta_reproduced_minus_reported": deltas}


def run_b008(orbits):
    _, LogisticRegression, accuracy_score, train_test_split, MLPClassifier = _sklearn()
    X, y = generate_z3_data_rich(n_samples=2000, orbits=orbits, seed=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    Phi_train = compute_orbit_histogram(X_train, orbits)
    Phi_test = compute_orbit_histogram(X_test, orbits)
    raw = LogisticRegression(max_iter=1000, random_state=42).fit(X_train, y_train)
    linear = LogisticRegression(max_iter=1000, random_state=42).fit(Phi_train, y_train)
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42, early_stopping=True, validation_fraction=0.15).fit(Phi_train, y_train)
    values = {
        "linear_raw": float(accuracy_score(y_test, raw.predict(X_test))),
        "linear_histogram": float(accuracy_score(y_test, linear.predict(Phi_test))),
        "mlp_histogram": float(accuracy_score(y_test, mlp.predict(Phi_test))),
    }
    status, deltas = rounded_match(values, REPORTED["B-008"])
    return {"status": status, "values": values, "reported": REPORTED["B-008"], "delta_reproduced_minus_reported": deltas}


def run_b009(orbits):
    err_g, err_g2, Phi_e, Phi_g, Phi_g2 = test_invariance_single(orbits)
    max_batch, err_batch_g, err_batch_g2 = test_invariance_batch(orbits, n_samples=100)
    rng = np.random.RandomState(99)
    discrimination = np.max(
        np.abs(
            compute_orbit_histogram(rng.randn(64), orbits)
            - compute_orbit_histogram(rng.randn(64), orbits)
        )
    )
    passed = max(err_g, err_g2) < 1e-14 and max_batch < 1e-13
    return {
        "status": "CLOSE_MATCH" if passed else "DIVERGENT",
        "note": "Zgodność kryteriów inwariantności; dokładny błąd maszynowy zależy od NumPy/platformy.",
        "values": {
            "single_error_g": float(err_g),
            "single_error_g2": float(err_g2),
            "batch_max_error": float(max_batch),
            "batch_error_g": float(err_batch_g),
            "batch_error_g2": float(err_batch_g2),
            "dimension": len(Phi_e),
            "energy_max_error": float(np.max(np.abs(Phi_e[:24] - Phi_g[:24]))),
            "mean_max_error": float(np.max(np.abs(Phi_e[24:48] - Phi_g[24:48]))),
            "amplitude_max_error": float(np.max(np.abs(Phi_e[48:72] - Phi_g[48:72]))),
            "discrimination": float(discrimination),
            "all_tests_passed": bool(passed),
        },
    }


RUNNERS = {
    "B-001": run_b001,
    "B-002": run_b002,
    "B-003": run_b003,
    "B-004": run_b004,
    "B-005": run_b005,
    "B-006": run_b006,
    "B-007": run_b007,
    "B-008": run_b008,
    "B-009": run_b009,
}


def make_report(payload: dict) -> str:
    lines = [
        "# Raport reprodukcji Etapu 03",
        "",
        f"Uruchomienie UTC: `{payload['run_utc']}`.",
        "",
        "| ID | Status | Uwagi |",
        "|---|---|---|",
    ]
    for experiment_id, result in payload["experiments"].items():
        note = result.get("audit_note", result.get("note", ""))
        lines.append(f"| {experiment_id} | {result['status']} | {note} |")
    lines.extend(
        [
            "",
            "## Interpretacja",
            "",
            "`DIVERGENT` nie oznacza automatycznie błędu nowego runnera. Oznacza, że wynik",
            "otrzymany z opublikowanego listingu nie zgadza się z wartością wydrukowaną",
            "w monografii w przyjętej dokładności. Szczegóły liczbowe są w `results.json`.",
            "",
            "Wyniki raportowane pozostają nietknięte w katalogach `historical/`; ten raport",
            "zawiera wyłącznie nową reprodukcję.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="tylko B-001--B-004 i B-009")
    parser.add_argument("--only", choices=IDS)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--no-zip", action="store_true")
    args = parser.parse_args()
    selected = [args.only] if args.only else (["B-001", "B-002", "B-003", "B-004", "B-009"] if args.smoke else IDS)
    run_time = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or (ROOT / "reproduced" / "stage_03_runs" / stamp)
    output_dir.mkdir(parents=True, exist_ok=True)
    orbits = compute_z3_orbits()
    results = {}
    for experiment_id in selected:
        print(f"RUN {experiment_id} ...", flush=True)
        results[experiment_id] = RUNNERS[experiment_id](orbits)
        print(f"{experiment_id}: {results[experiment_id]['status']}", flush=True)
    sklearn_version = None
    try:
        import sklearn
        sklearn_version = sklearn.__version__
    except ImportError:
        pass
    payload = {
        "stage": "03",
        "run_utc": run_time.isoformat(),
        "mode": "only" if args.only else "smoke" if args.smoke else "full",
        "selected": selected,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn_version,
            "processor_count": os.cpu_count(),
        },
        "experiments": results,
    }
    (output_dir / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "REPRODUCTION_REPORT_PL.md").write_text(make_report(payload), encoding="utf-8")
    latest = ROOT / "reproduced" / "stage_03_runs" / "LATEST_RUN.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(output_dir.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    zip_path = None
    if not args.no_zip:
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        base = artifacts / f"BOHN_ORIGINAL_STAGE_03_RESULTS_{stamp}"
        zip_path = Path(shutil.make_archive(str(base), "zip", root_dir=output_dir))
    print(f"RESULTS: {output_dir}")
    if zip_path:
        print(f"ZIP: {zip_path}")
    bad = any(result["status"] == "FAILED" for result in results.values())
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
