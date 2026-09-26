"""Jawne rekonstrukcje uzupełniające dla pięciu jednostek Etapu 07.

Kod nie jest źródłem historycznym. Implementuje zamrożone, możliwie proste
kontrakty wyprowadzone z opisów w rozdziale 5 monografii.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

Progress = Callable[[str], None]
N_PIXELS = 64


def _progress(message: str) -> None:
    print(message, flush=True)


def flip_horizontal(x: np.ndarray) -> np.ndarray:
    return x.reshape(-1, 8, 8)[:, :, ::-1].reshape(-1, 64)


def rotate_180(x: np.ndarray) -> np.ndarray:
    return np.rot90(x.reshape(-1, 8, 8), k=2, axes=(1, 2)).reshape(-1, 64)


def transform_to_perm(transform: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    indices = np.arange(N_PIXELS).reshape(1, N_PIXELS).astype(float)
    return transform(indices).astype(int).ravel()


TRUE_FLIP = transform_to_perm(flip_horizontal)
TRUE_ROT180 = transform_to_perm(rotate_180)


def make_labels(x: np.ndarray, seed: int = 42, noise: float = 0.10) -> np.ndarray:
    rng = np.random.default_rng(seed)
    af = np.abs(x - flip_horizontal(x))
    ar = np.abs(x - rotate_180(x))
    idx_f = rng.choice(N_PIXELS, size=10, replace=False)
    idx_r = rng.choice(N_PIXELS, size=10, replace=False)
    w_f = rng.uniform(0.5, 1.5, size=10)
    w_r = rng.uniform(0.5, 1.5, size=10)
    signal = af[:, idx_f] @ w_f + ar[:, idx_r] @ w_r
    signal += noise * rng.normal(size=len(x))
    return (signal > np.median(signal)).astype(int)


def digits_problem(label_seed: int = 42, split_seed: int = 42):
    x = load_digits().data.astype(np.float32) / 16.0
    y = make_labels(x, seed=label_seed)
    return train_test_split(x, y, test_size=0.30, random_state=split_seed, stratify=y)


def a_features(x: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    return np.abs(x - x[:, permutation])


def library_features(x: np.ndarray, permutations: list[np.ndarray]) -> np.ndarray:
    return np.concatenate([a_features(x, permutation) for permutation in permutations], axis=1)


def lr_accuracy(x_train, x_test, y_train, y_test) -> float:
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, solver="lbfgs"))
    model.fit(x_train, y_train)
    return float(accuracy_score(y_test, model.predict(x_test)))


def mutate_perm(permutation: np.ndarray, rng: np.random.Generator, swaps: int) -> np.ndarray:
    result = permutation.copy()
    for _ in range(swaps):
        i, j = rng.choice(len(result), size=2, replace=False)
        result[i], result[j] = result[j], result[i]
    return result


def crossover_perm(first: np.ndarray, second: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    start, stop = sorted(rng.choice(len(first), size=2, replace=False))
    child = np.full(len(first), -1, dtype=int)
    child[start:stop] = first[start:stop]
    used = set(child[start:stop])
    values = [value for value in second if value not in used]
    positions = np.flatnonzero(child == -1)
    child[positions] = values
    return child


def pair_accuracy(split, pair: tuple[np.ndarray, np.ndarray]) -> float:
    x_train, x_test, y_train, y_test = split
    return lr_accuracy(library_features(x_train, list(pair)), library_features(x_test, list(pair)), y_train, y_test)


def run_pl002r(config: dict, progress: Progress = _progress) -> dict:
    split = digits_problem(config.get("label_seed", 42), config.get("split_seed", 42))
    x_train, x_test, y_train, y_test = split
    baseline = lr_accuracy(x_train, x_test, y_train, y_test)
    flip = lr_accuracy(a_features(x_train, TRUE_FLIP), a_features(x_test, TRUE_FLIP), y_train, y_test)
    rot = lr_accuracy(a_features(x_train, TRUE_ROT180), a_features(x_test, TRUE_ROT180), y_train, y_test)
    true_pair = pair_accuracy(split, (TRUE_FLIP, TRUE_ROT180))
    rng = np.random.default_rng(config["evolution_seed"])
    population_size = config["population"]
    generations = config["generations"]
    elite_size = min(config.get("elite", 8), population_size)
    swaps = config.get("mutation_swaps", 4)
    population = [(rng.permutation(N_PIXELS), rng.permutation(N_PIXELS)) for _ in range(population_size)]
    history = []
    initial_best = None
    best_global = None
    for generation in range(generations):
        scored = sorted(((pair_accuracy(split, pair), pair) for pair in population), key=lambda row: row[0], reverse=True)
        if initial_best is None:
            initial_best = scored[0][0]
        if best_global is None or scored[0][0] > best_global[0]:
            best_global = scored[0]
        history.append({"generation": generation, "best": scored[0][0], "mean": float(np.mean([row[0] for row in scored]))})
        progress(f"PL-002R generation {generation + 1}/{generations} best={scored[0][0]:.4f}")
        elites = [row[1] for row in scored[:elite_size]]
        next_population = list(elites)
        while len(next_population) < population_size:
            parent_a = elites[rng.integers(0, elite_size)]
            parent_b = elites[rng.integers(0, elite_size)]
            child = []
            for index in range(2):
                if rng.random() < 0.5:
                    value = parent_a[index]
                else:
                    value = crossover_perm(parent_a[index], parent_b[index], rng)
                child.append(mutate_perm(value, rng, swaps))
            next_population.append((child[0], child[1]))
        population = next_population
    evolved = float(best_global[0])
    confirmed = evolved > baseline and evolved >= float(initial_best)
    return {
        "experiment_id": "PL-002R",
        "metrics": {"baseline": baseline, "true_flip": flip, "true_rot180": rot, "true_pair": true_pair, "initial_random_best_pair": float(initial_best), "evolved_best_pair": evolved, "gain_over_baseline": evolved - baseline, "gain_over_initial": evolved - float(initial_best)},
        "history": history,
        "primary_criterion_pass": confirmed,
        "status": "STRUCTURAL_RECONSTRUCTION_CONFIRMED" if confirmed else "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED",
    }


def run_pl003r(config: dict, progress: Progress = _progress) -> dict:
    split = digits_problem(config.get("label_seed", 42), config.get("split_seed", 42))
    x_train, x_test, y_train, y_test = split
    baseline = lr_accuracy(x_train, x_test, y_train, y_test)
    k_values = list(config["k_values"])
    rng = np.random.default_rng(config["seed"])
    permutations = [rng.permutation(N_PIXELS) for _ in range(max(k_values))]
    rows = []
    for k in k_values:
        accuracy = lr_accuracy(library_features(x_train, permutations[:k]), library_features(x_test, permutations[:k]), y_train, y_test)
        rows.append({"k": k, "accuracy": accuracy, "gain": accuracy - baseline})
        progress(f"PL-003R K={k} accuracy={accuracy:.4f}")
    accuracies = [row["accuracy"] for row in rows]
    overall_trend = float(np.polyfit(np.log(np.asarray(k_values, dtype=float)), accuracies, 1)[0]) if len(rows) > 1 else 0.0
    confirmed = rows[-1]["accuracy"] > rows[0]["accuracy"] and rows[-1]["accuracy"] > baseline and overall_trend > 0
    return {"experiment_id": "PL-003R", "metrics": {"baseline": baseline, "rows": rows, "log_k_trend": overall_trend}, "primary_criterion_pass": confirmed, "status": "STRUCTURAL_RECONSTRUCTION_CONFIRMED" if confirmed else "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED"}


def z3_permutation(dimension: int) -> np.ndarray:
    block = dimension // 3
    return np.concatenate([np.arange(block, 2 * block), np.arange(2 * block, 3 * block), np.arange(block)])


def z3_features(x: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    gx = x[:, permutation]
    g2x = gx[:, permutation]
    return np.concatenate([x + gx + g2x, np.abs(x - gx), np.abs(x - g2x)], axis=1)


def proportional_data(n: int, dimension: int, noise_std: float, seed: int):
    rng = np.random.RandomState(seed)
    x = rng.randn(n, dimension)
    permutation = z3_permutation(dimension)
    gx = x[:, permutation]
    g2x = gx[:, permutation]
    s3 = x + gx + g2x
    a1 = np.abs(x - gx)
    a2 = np.abs(x - g2x)
    scale = float(dimension)
    w1, w2, w3 = rng.randn(dimension) / scale, rng.randn(dimension) / scale, rng.randn(dimension) / scale
    signal = a1 @ w1 + a2 @ w2 + s3 @ w3
    y = (signal + rng.randn(n) * noise_std > np.median(signal)).astype(int)
    return x, y, permutation


def hd_one(n: int, dimension: int, noise_std: float, seed: int) -> tuple[float, float]:
    x, y, permutation = proportional_data(n, dimension, noise_std, seed)
    split = int(0.7 * n)
    raw = SGDClassifier(loss="log_loss", max_iter=500, random_state=seed, tol=1e-3)
    raw.fit(x[:split], y[:split])
    raw_accuracy = float(raw.score(x[split:], y[split:]))
    representation = z3_features(x, permutation)
    model = SGDClassifier(loss="log_loss", max_iter=500, random_state=seed, tol=1e-3)
    model.fit(representation[:split], y[:split])
    return raw_accuracy, float(model.score(representation[split:], y[split:]))


def run_hd003r(config: dict, progress: Progress = _progress) -> dict:
    rows = []
    for dimension in config["dimensions"]:
        values = []
        for seed in config["seeds"]:
            raw, sbohn = hd_one(config.get("n", 2000), dimension, config.get("noise_std", 0.1), seed)
            values.append((raw, sbohn))
            progress(f"HD-003R d={dimension} seed={seed} raw={raw:.4f} sbohn={sbohn:.4f}")
        array = np.asarray(values)
        rows.append({"dimension": dimension, "baseline": float(array[:, 0].mean()), "sbohn": float(array[:, 1].mean()), "gain": float((array[:, 1] - array[:, 0]).mean()), "wins": int(np.sum(array[:, 1] > array[:, 0])), "runs": len(values)})
    gains = [row["gain"] for row in rows]
    confirmed = all(row["wins"] == row["runs"] and row["gain"] > 0 for row in rows) and all(first > second for first, second in zip(gains, gains[1:]))
    return {"experiment_id": "HD-003R", "metrics": {"rows": rows}, "primary_criterion_pass": confirmed, "status": "STRUCTURAL_RECONSTRUCTION_CONFIRMED" if confirmed else "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED"}


def compression_representation(x: np.ndarray) -> np.ndarray:
    """Jawny kontrakt: dwa prawdziwe bloki asymetrii, łącznie 128 cech."""
    return library_features(x, [TRUE_FLIP, TRUE_ROT180])


def relu(value: np.ndarray) -> np.ndarray:
    return np.maximum(value, 0.0)


def autoencoder_bottleneck(model: MLPRegressor, x: np.ndarray) -> np.ndarray:
    hidden = relu(x @ model.coefs_[0] + model.intercepts_[0])
    return relu(hidden @ model.coefs_[1] + model.intercepts_[1])


def run_cmp001r(config: dict, progress: Progress = _progress) -> dict:
    seed = config["seed"]
    x_train, x_test, y_train, y_test = digits_problem(config.get("label_seed", 42), seed)
    rep_train, rep_test = compression_representation(x_train), compression_representation(x_test)
    scaler = StandardScaler().fit(rep_train)
    train_scaled, test_scaled = scaler.transform(rep_train), scaler.transform(rep_test)
    bottleneck = config.get("bottleneck", 48)
    pca = PCA(n_components=bottleneck, random_state=seed).fit(train_scaled)
    pca_accuracy = lr_accuracy(pca.transform(train_scaled), pca.transform(test_scaled), y_train, y_test)
    progress(f"CMP-001R PCA-{bottleneck} accuracy={pca_accuracy:.4f}")
    autoencoder = MLPRegressor(hidden_layer_sizes=tuple(config.get("autoencoder_hidden", [96, 48, 96])), activation="relu", solver="adam", max_iter=config.get("autoencoder_max_iter", 150), early_stopping=True, n_iter_no_change=15, random_state=seed)
    autoencoder.fit(train_scaled, train_scaled)
    ae_train = autoencoder_bottleneck(autoencoder, train_scaled)
    ae_test = autoencoder_bottleneck(autoencoder, test_scaled)
    ae_accuracy = lr_accuracy(ae_train, ae_test, y_train, y_test)
    progress(f"CMP-001R AE-{bottleneck} accuracy={ae_accuracy:.4f}")
    confirmed = pca_accuracy > ae_accuracy
    return {"experiment_id": "CMP-001R", "metrics": {"pca_accuracy": pca_accuracy, "autoencoder_accuracy": ae_accuracy, "pca_minus_autoencoder": pca_accuracy - ae_accuracy, "autoencoder_iterations": int(autoencoder.n_iter_)}, "primary_criterion_pass": confirmed, "status": "STRUCTURAL_RECONSTRUCTION_CONFIRMED" if confirmed else "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED"}


def run_cmp002r(config: dict, progress: Progress = _progress) -> dict:
    k_values = list(config["latent_dimensions"])
    seed_rows = []
    for seed in config["seeds"]:
        x_train, x_test, y_train, y_test = digits_problem(config.get("label_seed", 42), seed)
        rep_train, rep_test = compression_representation(x_train), compression_representation(x_test)
        baseline = lr_accuracy(x_train, x_test, y_train, y_test)
        full = lr_accuracy(rep_train, rep_test, y_train, y_test)
        scaler = StandardScaler().fit(rep_train)
        train_scaled, test_scaled = scaler.transform(rep_train), scaler.transform(rep_test)
        row = {"seed": seed, "baseline": baseline, "full": full, "pca": {}, "srl": {}}
        for k in k_values:
            pca = PCA(n_components=k, random_state=seed).fit(train_scaled)
            row["pca"][str(k)] = lr_accuracy(pca.transform(train_scaled), pca.transform(test_scaled), y_train, y_test)
            model = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(config.get("hidden_width", 32), k, config.get("hidden_width", 32)), activation="relu", solver="adam", max_iter=config.get("max_iter", 300), early_stopping=True, n_iter_no_change=20, random_state=seed))
            model.fit(rep_train, y_train)
            row["srl"][str(k)] = float(accuracy_score(y_test, model.predict(rep_test)))
            progress(f"CMP-002R seed={seed} k={k} pca={row['pca'][str(k)]:.4f} srl={row['srl'][str(k)]:.4f}")
        seed_rows.append(row)
    mean_baseline = float(np.mean([row["baseline"] for row in seed_rows]))
    mean_full = float(np.mean([row["full"] for row in seed_rows]))
    mean_pca = {str(k): float(np.mean([row["pca"][str(k)] for row in seed_rows])) for k in k_values}
    mean_srl = {str(k): float(np.mean([row["srl"][str(k)] for row in seed_rows])) for k in k_values}
    wins = {str(k): int(sum(row["srl"][str(k)] > row["pca"][str(k)] for row in seed_rows)) for k in k_values}
    confirmed = all(mean_srl[str(k)] > mean_pca[str(k)] for k in k_values) and mean_srl["2"] >= 0.90 * mean_full
    return {"experiment_id": "CMP-002R", "metrics": {"mean_baseline": mean_baseline, "mean_full": mean_full, "mean_pca": mean_pca, "mean_srl": mean_srl, "srl_wins_over_pca": wins, "runs": len(seed_rows), "seed_rows": seed_rows}, "primary_criterion_pass": confirmed, "status": "STRUCTURAL_RECONSTRUCTION_CONFIRMED" if confirmed else "STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED"}
