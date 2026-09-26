import numpy as np
import pandas as pd

from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# SBOHN-PL: Permutation Learning by Evolution
# Hidden target: rotate_180
# No torch required.
# ============================================================

IMAGE_SIZE = 8
N_PIXELS = 64


def reshape_images(X):
    return X.reshape(-1, IMAGE_SIZE, IMAGE_SIZE)


def flatten_images(X):
    return X.reshape(X.shape[0], -1)


def rotate_180_transform(X):
    img = reshape_images(X)
    return flatten_images(np.rot90(img, k=2, axes=(1, 2)))


def build_rotate_180_perm():
    indices = np.arange(N_PIXELS).reshape(1, N_PIXELS).astype(float)
    rotated = rotate_180_transform(indices)
    return rotated.astype(int).reshape(-1)


TRUE_PERM = build_rotate_180_perm()


def apply_perm(X, perm):
    return X[:, perm]


def sbohn_perm_features(X, perm):
    PX = apply_perm(X, perm)
    S = X + PX
    A = np.abs(X - PX)
    return np.concatenate([S, A], axis=1)


def make_hidden_rotate180_labels(X, seed=0, noise=0.10):
    rng = np.random.default_rng(seed)

    X_rot = rotate_180_transform(X)
    A = np.abs(X - X_rot)

    idx = rng.choice(N_PIXELS, size=12, replace=False)
    weights = rng.uniform(0.5, 1.5, size=len(idx))

    signal = A[:, idx] @ weights
    signal = signal + noise * rng.normal(size=len(X))

    threshold = np.median(signal)
    y = (signal > threshold).astype(int)

    return y


def evaluate_perm(X_train, X_test, y_train, y_test, perm):
    Xtr = sbohn_perm_features(X_train, perm)
    Xte = sbohn_perm_features(X_test, perm)

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=1500,
            solver="lbfgs"
        )
    )

    model.fit(Xtr, y_train)
    pred = model.predict(Xte)

    return accuracy_score(y_test, pred)


def permutation_similarity(p, q):
    return np.mean(p == q)


def mutate_perm(perm, rng, n_swaps=4):
    p = perm.copy()

    for _ in range(n_swaps):
        i, j = rng.choice(len(p), size=2, replace=False)
        p[i], p[j] = p[j], p[i]

    return p


def crossover_perm(parent1, parent2, rng):
    """
    Order crossover for permutations.
    """
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


def evolve_permutation(
    X_train,
    X_test,
    y_train,
    y_test,
    population_size=40,
    generations=25,
    elite_size=8,
    mutation_swaps=4,
    seed=0
):
    rng = np.random.default_rng(seed)

    population = [
        rng.permutation(N_PIXELS)
        for _ in range(population_size)
    ]

    history = []

    for gen in range(generations):
        scored = []

        for perm in population:
            acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
            sim = permutation_similarity(perm, TRUE_PERM)

            scored.append({
                "perm": perm,
                "accuracy": acc,
                "similarity_to_true": sim
            })

        scored = sorted(
            scored,
            key=lambda d: d["accuracy"],
            reverse=True
        )

        best = scored[0]

        history.append({
            "generation": gen,
            "best_accuracy": best["accuracy"],
            "best_similarity": best["similarity_to_true"],
            "mean_accuracy": np.mean([s["accuracy"] for s in scored]),
            "mean_similarity": np.mean([s["similarity_to_true"] for s in scored])
        })

        print(
            f"gen={gen:02d} "
            f"best_acc={best['accuracy']:.4f} "
            f"best_sim={best['similarity_to_true']:.4f} "
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

    final_scored = []

    for perm in population:
        acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
        sim = permutation_similarity(perm, TRUE_PERM)

        final_scored.append({
            "perm": perm,
            "accuracy": acc,
            "similarity_to_true": sim
        })

    final_scored = sorted(
        final_scored,
        key=lambda d: d["accuracy"],
        reverse=True
    )

    return final_scored[0], pd.DataFrame(history)


def evaluate_baseline_x(X_train, X_test, y_train, y_test):
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=1500,
            solver="lbfgs"
        )
    )

    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    return accuracy_score(y_test, pred)


def random_perm_scores(X_train, X_test, y_train, y_test, n_random=30, seed=0):
    rng = np.random.default_rng(seed)
    scores = []

    for _ in range(n_random):
        perm = rng.permutation(N_PIXELS)
        acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
        sim = permutation_similarity(perm, TRUE_PERM)

        scores.append((acc, sim))

    scores = np.array(scores)

    return {
        "random_mean_acc": scores[:, 0].mean(),
        "random_best_acc": scores[:, 0].max(),
        "random_mean_similarity": scores[:, 1].mean(),
        "random_best_similarity": scores[:, 1].max(),
    }


def main():
    seed = 42

    digits = load_digits()

    X = digits.data.astype(np.float32) / 16.0
    y = make_hidden_rotate180_labels(X, seed=seed, noise=0.10)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=seed,
        stratify=y
    )

    baseline_acc = evaluate_baseline_x(
        X_train,
        X_test,
        y_train,
        y_test
    )

    true_acc = evaluate_perm(
        X_train,
        X_test,
        y_train,
        y_test,
        TRUE_PERM
    )

    random_stats = random_perm_scores(
        X_train,
        X_test,
        y_train,
        y_test,
        n_random=30,
        seed=seed
    )

    print("======================================")
    print("SBOHN-PL: PERMUTATION LEARNING")
    print("======================================")
    print()
    print(f"Baseline x accuracy:       {baseline_acc:.4f}")
    print(f"True rotate180 accuracy:   {true_acc:.4f}")
    print(f"Random mean accuracy:      {random_stats['random_mean_acc']:.4f}")
    print(f"Random best accuracy:      {random_stats['random_best_acc']:.4f}")
    print()
    print("Starting evolutionary search...")
    print()

    best, history = evolve_permutation(
        X_train,
        X_test,
        y_train,
        y_test,
        population_size=40,
        generations=25,
        elite_size=8,
        mutation_swaps=4,
        seed=seed
    )

    print()
    print("======================================")
    print("FINAL RESULT")
    print("======================================")
    print(f"Best evolved accuracy:       {best['accuracy']:.4f}")
    print(f"Best evolved similarity:     {best['similarity_to_true']:.4f}")
    print()
    print(f"Gain over baseline:          {best['accuracy'] - baseline_acc:.4f}")
    print(f"Gain over random mean:       {best['accuracy'] - random_stats['random_mean_acc']:.4f}")
    print(f"Gap to true rotate180:       {true_acc - best['accuracy']:.4f}")
    print()
    print("History:")
    print(history.to_string(index=False))


if __name__ == "__main__":
    main()
