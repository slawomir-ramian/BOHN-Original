import time
import numpy as np
import pandas as pd

from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

IMAGE_SIZE = 8
N_PIXELS = 64


def reshape_images(X):
    return X.reshape(-1, IMAGE_SIZE, IMAGE_SIZE)


def flatten_images(X):
    return X.reshape(X.shape[0], -1)


def flip_horizontal_transform(X):
    img = reshape_images(X)
    return flatten_images(img[:, :, ::-1])


def rotate_180_transform(X):
    img = reshape_images(X)
    return flatten_images(np.rot90(img, k=2, axes=(1, 2)))


def transform_to_perm(transform_fn):
    idx = np.arange(N_PIXELS).reshape(1, N_PIXELS).astype(float)
    transformed = transform_fn(idx)
    return transformed.astype(int).reshape(-1)


TRUE_FLIP = transform_to_perm(flip_horizontal_transform)
TRUE_ROT180 = transform_to_perm(rotate_180_transform)


def make_labels(X, seed=0, noise=0.10):
    rng = np.random.default_rng(seed)

    XF = flip_horizontal_transform(X)
    XR = rotate_180_transform(X)

    AF = np.abs(X - XF)
    AR = np.abs(X - XR)

    idx_F = rng.choice(N_PIXELS, size=10, replace=False)
    idx_R = rng.choice(N_PIXELS, size=10, replace=False)

    w_F = rng.uniform(0.5, 1.5, size=10)
    w_R = rng.uniform(0.5, 1.5, size=10)

    signal = AF[:, idx_F] @ w_F + AR[:, idx_R] @ w_R
    signal = signal + noise * rng.normal(size=len(X))

    threshold = np.median(signal)
    return (signal > threshold).astype(int)


def apply_perm(X, perm):
    return X[:, perm]


def A_features(X, perm):
    return np.abs(X - apply_perm(X, perm))


def evaluate_features(X_train, X_test, y_train, y_test):
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=3000, solver="lbfgs")
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return accuracy_score(y_test, pred)


def evaluate_perm(X_train, X_test, y_train, y_test, perm):
    return evaluate_features(
        A_features(X_train, perm),
        A_features(X_test, perm),
        y_train,
        y_test
    )


def perm_similarity(p, q):
    return np.mean(p == q)


def mutate_perm(perm, rng, n_swaps=4):
    p = perm.copy()
    for _ in range(n_swaps):
        i, j = rng.choice(len(p), size=2, replace=False)
        p[i], p[j] = p[j], p[i]
    return p


def crossover_perm(parent1, parent2, rng):
    n = len(parent1)
    a, b = sorted(rng.choice(n, size=2, replace=False))
    child = -np.ones(n, dtype=int)
    child[a:b] = parent1[a:b]
    used = set(child[a:b])
    fill_values = [x for x in parent2 if x not in used]
    fill_positions = [i for i in range(n) if child[i] == -1]
    for pos, val in zip(fill_positions, fill_values):
        child[pos] = val
    return child


def evolve_best_perm(
    X_train,
    X_test,
    y_train,
    y_test,
    population_size=100,
    generations=50,
    elite_size=10,
    mutation_swaps=4,
    seed=42
):
    rng = np.random.default_rng(seed)
    population = [rng.permutation(N_PIXELS) for _ in range(population_size)]
    best_global = None
    history = []

    for gen in range(generations):
        scored = []

        for perm in population:
            acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
            scored.append({
                "perm": perm,
                "accuracy": acc,
                "sim_flip": perm_similarity(perm, TRUE_FLIP),
                "sim_rot": perm_similarity(perm, TRUE_ROT180),
                "best_true_sim": max(
                    perm_similarity(perm, TRUE_FLIP),
                    perm_similarity(perm, TRUE_ROT180)
                )
            })

        scored = sorted(scored, key=lambda d: d["accuracy"], reverse=True)

        if best_global is None or scored[0]["accuracy"] > best_global["accuracy"]:
            best_global = scored[0]

        best = scored[0]

        history.append({
            "generation": gen,
            "best_accuracy": best["accuracy"],
            "best_true_sim": best["best_true_sim"],
            "sim_flip": best["sim_flip"],
            "sim_rot": best["sim_rot"],
            "mean_accuracy": np.mean([s["accuracy"] for s in scored])
        })

        print(
            f"gen={gen:02d} best_acc={best['accuracy']:.4f} "
            f"sim_flip={best['sim_flip']:.4f} "
            f"sim_rot={best['sim_rot']:.4f} "
            f"mean_acc={history[-1]['mean_accuracy']:.4f}"
        )

        elites = [s["perm"] for s in scored[:elite_size]]
        new_population = elites.copy()

        while len(new_population) < population_size:
            if rng.random() < 0.5:
                parent = elites[rng.integers(0, elite_size)]
                child = mutate_perm(parent, rng, n_swaps=mutation_swaps)
            else:
                p1 = elites[rng.integers(0, elite_size)]
                p2 = elites[rng.integers(0, elite_size)]
                child = crossover_perm(p1, p2, rng)
                child = mutate_perm(child, rng, n_swaps=mutation_swaps)
            new_population.append(child)

        population = new_population

    return best_global, pd.DataFrame(history)


def center_columns(X):
    return X - X.mean(axis=0, keepdims=True)


def feature_abs_corr(A, B, eps=1e-12):
    A0 = center_columns(A)
    B0 = center_columns(B)
    num = np.sum(A0 * B0, axis=0)
    den = np.sqrt(np.sum(A0 * A0, axis=0) * np.sum(B0 * B0, axis=0)) + eps
    corr = num / den
    return {
        "mean_abs_corr": float(np.mean(np.abs(corr))),
        "median_abs_corr": float(np.median(np.abs(corr))),
        "max_abs_corr": float(np.max(np.abs(corr))),
    }


def sample_cosine_similarity(A, B, eps=1e-12):
    num = np.sum(A * B, axis=1)
    den = np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1) + eps
    cos = num / den
    return {
        "mean_sample_cosine": float(np.mean(cos)),
        "median_sample_cosine": float(np.median(cos)),
        "min_sample_cosine": float(np.min(cos)),
        "max_sample_cosine": float(np.max(cos)),
    }


def linear_cka(A, B, eps=1e-12):
    A0 = center_columns(A)
    B0 = center_columns(B)
    hsic = np.linalg.norm(A0.T @ B0, ord="fro") ** 2
    norm_a = np.linalg.norm(A0.T @ A0, ord="fro")
    norm_b = np.linalg.norm(B0.T @ B0, ord="fro")
    return float(hsic / (norm_a * norm_b + eps))


def compare_representations(name, A, B):
    corr = feature_abs_corr(A, B)
    cos = sample_cosine_similarity(A, B)
    cka = linear_cka(A, B)
    row = {"comparison": name, "linear_cka": cka}
    row.update(corr)
    row.update(cos)
    return row


def main():
    seed = 42

    digits = load_digits()
    X = digits.data.astype(np.float32) / 16.0
    y = make_labels(X, seed=seed, noise=0.10)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=seed, stratify=y
    )

    print("======================================")
    print("SBOHN-AR REPRESENTATION CORRELATION TEST")
    print("======================================")
    print()

    baseline_acc = evaluate_features(X_train, X_test, y_train, y_test)
    flip_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_FLIP)
    rot_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_ROT180)

    print(f"Baseline x accuracy:  {baseline_acc:.4f}")
    print(f"True flip accuracy:   {flip_acc:.4f}")
    print(f"True rot accuracy:    {rot_acc:.4f}")
    print()
    print("Evolving best permutation...")
    print()

    t0 = time.perf_counter()
    best, history = evolve_best_perm(
        X_train,
        X_test,
        y_train,
        y_test,
        population_size=100,
        generations=50,
        elite_size=10,
        mutation_swaps=4,
        seed=seed
    )
    elapsed = time.perf_counter() - t0

    best_perm = best["perm"]
    best_acc = best["accuracy"]
    sim_flip = perm_similarity(best_perm, TRUE_FLIP)
    sim_rot = perm_similarity(best_perm, TRUE_ROT180)

    A_best = A_features(X_test, best_perm)
    A_flip = A_features(X_test, TRUE_FLIP)
    A_rot = A_features(X_test, TRUE_ROT180)

    rows = []
    rows.append(compare_representations("best_vs_flip", A_best, A_flip))
    rows.append(compare_representations("best_vs_rot180", A_best, A_rot))
    rows.append(compare_representations("flip_vs_rot180", A_flip, A_rot))

    comparison = pd.DataFrame(rows)

    print()
    print("======================================")
    print("FINAL RESULT")
    print("======================================")
    print()
    print(f"Best evolved accuracy: {best_acc:.4f}")
    print(f"Best sim to flip:      {sim_flip:.4f}")
    print(f"Best sim to rot180:    {sim_rot:.4f}")
    print(f"Elapsed time:          {elapsed:.2f} sec")
    print()
    print("Representation similarity:")
    print(comparison.to_string(index=False))

    print()
    print("History:")
    print(history.to_string(index=False))


if __name__ == "__main__":
    main()
