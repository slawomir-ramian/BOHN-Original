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


def sbohn_A_features(X, perm):
    PX = apply_perm(X, perm)
    return np.abs(X - PX)


def make_model():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=3000, solver="lbfgs")
    )


def evaluate_features(X_train, X_test, y_train, y_test):
    model = make_model()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return accuracy_score(y_test, pred)


def evaluate_perm(X_train, X_test, y_train, y_test, perm):
    Phi_train = sbohn_A_features(X_train, perm)
    Phi_test = sbohn_A_features(X_test, perm)
    return evaluate_features(Phi_train, Phi_test, y_train, y_test)


def perm_similarity(p, q):
    return np.mean(p == q)


def best_true_similarity(p):
    sim_flip = perm_similarity(p, TRUE_FLIP)
    sim_rot = perm_similarity(p, TRUE_ROT180)
    return max(sim_flip, sim_rot), sim_flip, sim_rot


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


def evolve_permutations(
    X_train,
    X_test,
    y_train,
    y_test,
    population_size=100,
    generations=50,
    elite_size=10,
    mutation_swaps=4,
    seed=0
):
    rng = np.random.default_rng(seed)

    population = [rng.permutation(N_PIXELS) for _ in range(population_size)]
    history = []

    for gen in range(generations):
        scored = []

        for perm in population:
            acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
            best_sim, sim_flip, sim_rot = best_true_similarity(perm)

            scored.append({
                "perm": perm,
                "accuracy": acc,
                "best_true_similarity": best_sim,
                "flip_similarity": sim_flip,
                "rot180_similarity": sim_rot
            })

        scored = sorted(scored, key=lambda d: d["accuracy"], reverse=True)
        best = scored[0]

        history.append({
            "generation": gen,
            "best_accuracy": best["accuracy"],
            "best_true_similarity": best["best_true_similarity"],
            "best_flip_similarity": best["flip_similarity"],
            "best_rot180_similarity": best["rot180_similarity"],
            "mean_accuracy": np.mean([s["accuracy"] for s in scored]),
            "mean_true_similarity": np.mean([s["best_true_similarity"] for s in scored]),
        })

        print(
            f"gen={gen:02d} "
            f"best_acc={best['accuracy']:.4f} "
            f"best_sim={best['best_true_similarity']:.4f} "
            f"flip={best['flip_similarity']:.4f} "
            f"rot={best['rot180_similarity']:.4f} "
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
        best_sim, sim_flip, sim_rot = best_true_similarity(perm)
        final_scored.append({
            "perm": perm,
            "accuracy": acc,
            "best_true_similarity": best_sim,
            "flip_similarity": sim_flip,
            "rot180_similarity": sim_rot
        })

    final_scored = sorted(final_scored, key=lambda d: d["accuracy"], reverse=True)
    return final_scored[0], pd.DataFrame(history)


def random_population_stats(X_train, X_test, y_train, y_test, n_random=100, seed=0):
    rng = np.random.default_rng(seed)
    rows = []

    for _ in range(n_random):
        perm = rng.permutation(N_PIXELS)
        acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
        best_sim, sim_flip, sim_rot = best_true_similarity(perm)
        rows.append({
            "accuracy": acc,
            "best_true_similarity": best_sim,
            "flip_similarity": sim_flip,
            "rot180_similarity": sim_rot
        })

    df = pd.DataFrame(rows)
    return {
        "random_mean_acc": df["accuracy"].mean(),
        "random_best_acc": df["accuracy"].max(),
        "random_mean_sim": df["best_true_similarity"].mean(),
        "random_best_sim": df["best_true_similarity"].max(),
    }


def main():
    seed = 42

    digits = load_digits()
    X = digits.data.astype(np.float32) / 16.0
    y = make_labels(X, seed=seed, noise=0.10)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=seed, stratify=y
    )

    baseline_acc = evaluate_features(X_train, X_test, y_train, y_test)
    true_flip_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_FLIP)
    true_rot_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_ROT180)
    random_stats = random_population_stats(
        X_train, X_test, y_train, y_test, n_random=100, seed=seed
    )

    print("======================================")
    print("SBOHN-AR v1: EVOLUTIONARY GENERATION")
    print("======================================")
    print()
    print(f"Baseline x accuracy:     {baseline_acc:.4f}")
    print(f"True flip accuracy:      {true_flip_acc:.4f}")
    print(f"True rot180 accuracy:    {true_rot_acc:.4f}")
    print(f"Random mean accuracy:    {random_stats['random_mean_acc']:.4f}")
    print(f"Random best accuracy:    {random_stats['random_best_acc']:.4f}")
    print(f"Random mean similarity:  {random_stats['random_mean_sim']:.4f}")
    print(f"Random best similarity:  {random_stats['random_best_sim']:.4f}")
    print()
    print("Starting evolution...")
    print()

    t0 = time.perf_counter()
    best, history = evolve_permutations(
        X_train, X_test, y_train, y_test,
        population_size=100,
        generations=50,
        elite_size=10,
        mutation_swaps=4,
        seed=seed
    )
    elapsed = time.perf_counter() - t0

    print()
    print("======================================")
    print("FINAL RESULT")
    print("======================================")
    print(f"Best evolved accuracy:       {best['accuracy']:.4f}")
    print(f"Best evolved best similarity:{best['best_true_similarity']:.4f}")
    print(f"Best evolved flip similarity:{best['flip_similarity']:.4f}")
    print(f"Best evolved rot similarity: {best['rot180_similarity']:.4f}")
    print(f"Elapsed time:                {elapsed:.2f} sec")
    print()
    print(f"Gain over baseline:          {best['accuracy'] - baseline_acc:.4f}")
    print(f"Gain over random mean:       {best['accuracy'] - random_stats['random_mean_acc']:.4f}")
    print(f"Gain over random best:       {best['accuracy'] - random_stats['random_best_acc']:.4f}")
    print()
    print("History:")
    print(history.to_string(index=False))


if __name__ == "__main__":
    main()
