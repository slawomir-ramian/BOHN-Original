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


def true_similarity(p):
    sim_flip = perm_similarity(p, TRUE_FLIP)
    sim_rot = perm_similarity(p, TRUE_ROT180)
    return {
        "sim_flip": sim_flip,
        "sim_rot180": sim_rot,
        "best_true_sim": max(sim_flip, sim_rot)
    }


def center_columns(X):
    return X - X.mean(axis=0, keepdims=True)


def linear_cka(A, B, eps=1e-12):
    A0 = center_columns(A)
    B0 = center_columns(B)
    hsic = np.linalg.norm(A0.T @ B0, ord="fro") ** 2
    norm_a = np.linalg.norm(A0.T @ A0, ord="fro")
    norm_b = np.linalg.norm(B0.T @ B0, ord="fro")
    return float(hsic / (norm_a * norm_b + eps))


def mean_sample_cosine(A, B, eps=1e-12):
    num = np.sum(A * B, axis=1)
    den = np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1) + eps
    return float(np.mean(num / den))


def feature_mean_abs_corr(A, B, eps=1e-12):
    A0 = center_columns(A)
    B0 = center_columns(B)
    num = np.sum(A0 * B0, axis=0)
    den = np.sqrt(np.sum(A0 * A0, axis=0) * np.sum(B0 * B0, axis=0)) + eps
    corr = num / den
    return float(np.mean(np.abs(corr)))


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
    population_size=80,
    generations=35,
    elite_size=8,
    mutation_swaps=4,
    seed=0
):
    rng = np.random.default_rng(seed)
    population = [rng.permutation(N_PIXELS) for _ in range(population_size)]
    best_global = None

    for gen in range(generations):
        scored = []

        for perm in population:
            acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
            scored.append({"perm": perm, "accuracy": acc})

        scored = sorted(scored, key=lambda d: d["accuracy"], reverse=True)

        if best_global is None or scored[0]["accuracy"] > best_global["accuracy"]:
            best_global = scored[0]

        if gen % 5 == 0 or gen == generations - 1:
            print(
                f"seed={seed:02d} gen={gen:02d} "
                f"best_acc={scored[0]['accuracy']:.4f} "
                f"global_best={best_global['accuracy']:.4f}"
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

    return best_global


def pairwise_analysis(best_rows, X_reference):
    rows = []
    reps = [A_features(X_reference, row["perm"]) for row in best_rows]
    n = len(best_rows)

    for i in range(n):
        for j in range(i + 1, n):
            p_i = best_rows[i]["perm"]
            p_j = best_rows[j]["perm"]

            A_i = reps[i]
            A_j = reps[j]

            rows.append({
                "i": i,
                "j": j,
                "acc_i": best_rows[i]["accuracy"],
                "acc_j": best_rows[j]["accuracy"],
                "acc_abs_diff": abs(best_rows[i]["accuracy"] - best_rows[j]["accuracy"]),
                "perm_similarity": perm_similarity(p_i, p_j),
                "linear_cka": linear_cka(A_i, A_j),
                "mean_sample_cosine": mean_sample_cosine(A_i, A_j),
                "feature_mean_abs_corr": feature_mean_abs_corr(A_i, A_j),
            })

    return pd.DataFrame(rows)


def main():
    label_seed = 42

    n_runs = 20
    evolution_seeds = range(n_runs)

    population_size = 80
    generations = 35
    elite_size = 8
    mutation_swaps = 4

    print("======================================")
    print("SBOHN-AR EQUIVALENCE CLASS TEST")
    print("======================================")
    print()

    digits = load_digits()
    X = digits.data.astype(np.float32) / 16.0
    y = make_labels(X, seed=label_seed, noise=0.10)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=label_seed, stratify=y
    )

    baseline_acc = evaluate_features(X_train, X_test, y_train, y_test)
    flip_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_FLIP)
    rot_acc = evaluate_perm(X_train, X_test, y_train, y_test, TRUE_ROT180)

    print(f"Baseline accuracy:     {baseline_acc:.4f}")
    print(f"True flip accuracy:    {flip_acc:.4f}")
    print(f"True rot180 accuracy:  {rot_acc:.4f}")
    print()
    print("Running evolutionary searches...")
    print()

    t0 = time.perf_counter()
    best_rows = []

    for run_seed in evolution_seeds:
        best = evolve_best_perm(
            X_train,
            X_test,
            y_train,
            y_test,
            population_size=population_size,
            generations=generations,
            elite_size=elite_size,
            mutation_swaps=mutation_swaps,
            seed=run_seed
        )

        sim = true_similarity(best["perm"])

        row = {
            "run_seed": run_seed,
            "accuracy": best["accuracy"],
            "perm": best["perm"],
        }
        row.update(sim)
        best_rows.append(row)

    elapsed = time.perf_counter() - t0

    best_df = pd.DataFrame([
        {
            "run_seed": row["run_seed"],
            "accuracy": row["accuracy"],
            "sim_flip": row["sim_flip"],
            "sim_rot180": row["sim_rot180"],
            "best_true_sim": row["best_true_sim"]
        }
        for row in best_rows
    ])

    pairwise = pairwise_analysis(best_rows, X_test)

    pairwise_summary = pairwise.agg({
        "acc_abs_diff": ["mean", "std", "min", "max"],
        "perm_similarity": ["mean", "std", "min", "max"],
        "linear_cka": ["mean", "std", "min", "max"],
        "mean_sample_cosine": ["mean", "std", "min", "max"],
        "feature_mean_abs_corr": ["mean", "std", "min", "max"],
    })

    print()
    print("======================================")
    print("BEST PER RUN")
    print("======================================")
    print(best_df.to_string(index=False))

    print()
    print("======================================")
    print("BEST RUN SUMMARY")
    print("======================================")
    print(best_df.agg(["mean", "std", "min", "max"]).to_string())

    print()
    print("======================================")
    print("PAIRWISE EQUIVALENCE SUMMARY")
    print("======================================")
    print(pairwise_summary.to_string())

    print()
    print("======================================")
    print("FINAL INTERPRETATION NUMBERS")
    print("======================================")
    print(f"Runs:                         {n_runs}")
    print(f"Elapsed time:                 {elapsed:.2f} sec")
    print(f"Mean evolved accuracy:         {best_df['accuracy'].mean():.4f}")
    print(f"Std evolved accuracy:          {best_df['accuracy'].std():.4f}")
    print(f"Mean best true similarity:     {best_df['best_true_sim'].mean():.4f}")
    print(f"Mean pairwise perm similarity: {pairwise['perm_similarity'].mean():.4f}")
    print(f"Mean pairwise CKA:             {pairwise['linear_cka'].mean():.4f}")
    print(f"Mean pairwise cosine:          {pairwise['mean_sample_cosine'].mean():.4f}")
    print(f"Mean pairwise abs corr:        {pairwise['feature_mean_abs_corr'].mean():.4f}")
    print()
    print("Pairwise rows head:")
    print(pairwise.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
