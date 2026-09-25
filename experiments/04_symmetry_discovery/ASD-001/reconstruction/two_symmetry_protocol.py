"""Jawna rekonstrukcja hipotezy dwóch symetrii dla ASD-001R.

Ten plik nie zastępuje historycznego listingu ASD-001. Definiuje nowy,
oznaczony protokół badawczy, w którym obie deklarowane symetrie rzeczywiście
uczestniczą w generowaniu etykiety.
"""
from __future__ import annotations

import time
import warnings

import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


TRUE_NAMES = ("flip_horizontal", "rotate_180")


def flip_horizontal(values):
    return np.asarray(values).reshape(-1, 8, 8)[:, :, ::-1].reshape(-1, 64)


def rotate_180(values):
    return np.asarray(values).reshape(-1, 8, 8)[:, ::-1, ::-1].reshape(-1, 64)


def random_permutation(values, seed):
    permutation = np.random.default_rng(seed).permutation(values.shape[1])
    return np.asarray(values)[:, permutation]


def asymmetry(values, transformed):
    return np.abs(np.asarray(values) - np.asarray(transformed))


def standardize(values):
    values = np.asarray(values, dtype=np.float64)
    deviation = float(values.std())
    if deviation == 0.0:
        raise ValueError("Nie można standaryzować sygnału o zerowej wariancji.")
    return (values - float(values.mean())) / deviation


def make_two_symmetry_labels(values, label_seed=42):
    """Etykieta zależna jawnie i symetrycznie od obu prawdziwych bloków."""
    values = np.asarray(values, dtype=np.float64)
    flip_block = asymmetry(values, flip_horizontal(values))
    rotate_block = asymmetry(values, rotate_180(values))
    rng = np.random.default_rng(label_seed)
    flip_weights = rng.standard_normal(values.shape[1])
    rotate_weights = rng.standard_normal(values.shape[1])
    flip_signal = standardize(flip_block @ flip_weights)
    rotate_signal = standardize(rotate_block @ rotate_weights)
    combined = flip_signal + rotate_signal
    labels = (combined > np.median(combined)).astype(int)
    telemetry = {
        "label_seed": label_seed,
        "flip_signal_std": float(flip_signal.std()),
        "rotate_signal_std": float(rotate_signal.std()),
        "signal_correlation": float(np.corrcoef(flip_signal, rotate_signal)[0, 1]),
        "positive_fraction": float(labels.mean()),
    }
    return labels, flip_signal, rotate_signal, telemetry


def candidate_blocks(values, split_seed, random_count):
    values = np.asarray(values, dtype=np.float64)
    blocks = {
        "flip_horizontal": asymmetry(values, flip_horizontal(values)),
        "rotate_180": asymmetry(values, rotate_180(values)),
    }
    for index in range(random_count):
        name = f"rand_{index:02d}"
        permutation_seed = split_seed * 10000 + index
        transformed = random_permutation(values, permutation_seed)
        blocks[name] = asymmetry(values, transformed)
    return blocks


def shuffled_names(blocks, split_seed, c_value):
    """Porządek bloków niezależny od nazw i deterministyczny dla zadania."""
    names = list(blocks)
    order_seed = split_seed * 100000 + int(round(c_value * 10000)) + 1701
    np.random.default_rng(order_seed).shuffle(names)
    return names, order_seed


def strict_ranking(importances, names, epsilon=1e-10):
    """Zera są nierozstrzygniętym remisem, a nie sztuczną rangą alfabetyczną."""
    positive = [name for name in names if importances[name] > epsilon]
    positive.sort(key=lambda name: (-importances[name], names.index(name)))
    zero = [name for name in names if importances[name] <= epsilon]
    ranks = {name: index + 1 for index, name in enumerate(positive)}
    for name in zero:
        ranks[name] = None
    return positive, ranks, zero


def oracle_ablation(flip_signal, rotate_signal, labels, split_seed):
    """Tania kontrola, czy połączenie sygnałów wnosi więcej niż każdy osobno."""
    indices = np.arange(len(labels))
    train, test = train_test_split(
        indices, test_size=0.3, random_state=split_seed, stratify=labels
    )
    designs = {
        "flip_only": flip_signal[:, None],
        "rotate_only": rotate_signal[:, None],
        "combined": np.column_stack([flip_signal, rotate_signal]),
    }
    scores = {}
    coefficients = {}
    for name, design in designs.items():
        model = LogisticRegression(C=1000.0, solver="lbfgs", max_iter=1000)
        model.fit(design[train], labels[train])
        scores[name] = float(model.score(design[test], labels[test]))
        coefficients[name] = [float(value) for value in model.coef_[0]]
    scores["combined_gain"] = float(
        scores["combined"] - max(scores["flip_only"], scores["rotate_only"])
    )
    return {"accuracy": scores, "coefficients": coefficients}


def fit_pilot_task(task):
    c_value, split_seed, random_count, max_iter = task
    started = time.perf_counter()
    values = load_digits().data.astype(np.float64)
    labels, flip_signal, rotate_signal, telemetry = make_two_symmetry_labels(values)
    train_x, test_x, train_y, test_y = train_test_split(
        values,
        labels,
        test_size=0.3,
        random_state=split_seed,
        stratify=labels,
    )
    train_blocks = candidate_blocks(train_x, split_seed, random_count)
    test_blocks = candidate_blocks(test_x, split_seed, random_count)
    names, order_seed = shuffled_names(train_blocks, split_seed, c_value)
    design_train = np.hstack([train_blocks[name] for name in names])
    design_test = np.hstack([test_blocks[name] for name in names])
    classifier = LogisticRegression(
        C=c_value,
        l1_ratio=1.0,
        solver="saga",
        max_iter=max_iter,
        random_state=split_seed,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        classifier.fit(design_train, train_y)
    importances = {}
    for index, name in enumerate(names):
        block = slice(index * 64, (index + 1) * 64)
        importances[name] = float(np.abs(classifier.coef_[:, block]).sum())
    ranking, ranks, unresolved = strict_ranking(importances, names)
    random_importance = max(
        (value for name, value in importances.items() if name.startswith("rand_")),
        default=0.0,
    )
    true_importances = {name: importances[name] for name in TRUE_NAMES}
    return {
        "C": c_value,
        "seed": split_seed,
        "accuracy": float(classifier.score(design_test, test_y)),
        "candidate_order_seed": order_seed,
        "candidate_order": names,
        "top_candidates": ranking[:10],
        "true_ranks": {name: ranks[name] for name in TRUE_NAMES},
        "true_importances": true_importances,
        "max_random_importance": random_importance,
        "min_true_margin_over_best_random": float(
            min(true_importances.values()) - random_importance
        ),
        "nonzero_blocks": len(ranking),
        "unresolved_zero_blocks": len(unresolved),
        "warning_types": [type(item.message).__name__ for item in caught],
        "label_telemetry": telemetry,
        "oracle_ablation": oracle_ablation(
            flip_signal, rotate_signal, labels, split_seed
        ),
        "duration_seconds": round(time.perf_counter() - started, 6),
    }
