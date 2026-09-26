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

N_GENERATED_KEEP = 20
N_RANDOM_BACKGROUND = 79
TOTAL_BLOCKS = N_GENERATED_KEEP + N_RANDOM_BACKGROUND


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
    return np.abs(X - apply_perm(X, perm))


def build_A_features(X, perms):
    blocks = []
    for perm in perms:
        blocks.append(sbohn_A_features(X, perm))
    return np.concatenate(blocks, axis=1)


def perm_similarity(p, q):
    return np.mean(p == q)


def best_true_similarity(p):
    sim_flip = perm_similarity(p, TRUE_FLIP)
    sim_rot = perm_similarity(p, TRUE_ROT180)
    return max(sim_flip, sim_rot), sim_flip, sim_rot


def make_lr_model():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=3000, solver="lbfgs")
    )


def evaluate_features(X_train, X_test, y_train, y_test):
    model = make_lr_model()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return accuracy_score(y_test, pred)


def evaluate_perm(X_train, X_test, y_train, y_test, perm):
    return evaluate_features(
        sbohn_A_features(X_train, perm),
        sbohn_A_features(X_test, perm),
        y_train,
        y_test
    )


def evaluate_perm_set(X_train, X_test, y_train, y_test, perms):
    return evaluate_features(
        build_A_features(X_train, perms),
        build_A_features(X_test, perms),
        y_train,
        y_test
    )


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


def evolve_population(
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
            "mean_true_similarity": np.mean([s["best_true_similarity"] for s in scored])
        })

        print(
            f"gen={gen:02d} best_acc={best['accuracy']:.4f} "
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
    return scored, pd.DataFrame(history)


def fit_l1_model(X_train, y_train, C=0.10):
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            penalty="l1",
            solver="saga",
            C=C,
            max_iter=5000,
            tol=1e-4,
            n_jobs=-1
        )
    )
    model.fit(X_train, y_train)
    return model


def block_importance_from_pipeline(model, n_blocks, block_size):
    clf = model.named_steps["logisticregression"]
    coef = clf.coef_[0]
    rows = []

    for i in range(n_blocks):
        start = i * block_size
        end = (i + 1) * block_size
        block_coef = coef[start:end]
        rows.append({
            "block": i,
            "importance_l1": np.sum(np.abs(block_coef)),
            "nonzero_coeffs": int(np.sum(np.abs(block_coef) > 1e-10))
        })

    return pd.DataFrame(rows)


def make_random_perms(n, seed):
    rng = np.random.default_rng(seed)
    return [rng.permutation(N_PIXELS) for _ in range(n)]


def main():
    seed = 42
    C_l1 = 0.10

    population_size = 100
    generations = 50
    elite_size = 10
    mutation_swaps = 4

    digits = load_digits()
    X = digits.data.astype(np.float32) / 16.0
    y = make_labels(X, seed=seed, noise=0.10)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=seed, stratify=y
    )

    baseline_acc = evaluate_features(X_train, X_test, y_train, y_test)
    true_pair_acc = evaluate_perm_set(X_train, X_test, y_train, y_test, [TRUE_FLIP, TRUE_ROT180])

    random_99_perms = make_random_perms(TOTAL_BLOCKS, seed=seed + 1000)
    random_99_acc = evaluate_perm_set(X_train, X_test, y_train, y_test, random_99_perms)

    print("======================================")
    print("SBOHN-AR v2: GENERATE -> REPRESENT -> SELECT")
    print("======================================")
    print()
    print(f"Baseline x accuracy:        {baseline_acc:.4f}")
    print(f"True pair accuracy:         {true_pair_acc:.4f}")
    print(f"Random 99 accuracy:         {random_99_acc:.4f}")
    print()
    print("Phase 1: evolving permutation library...")
    print()

    t0 = time.perf_counter()
    scored_population, history = evolve_population(
        X_train,
        X_test,
        y_train,
        y_test,
        population_size=population_size,
        generations=generations,
        elite_size=elite_size,
        mutation_swaps=mutation_swaps,
        seed=seed
    )
    evolve_time = time.perf_counter() - t0

    generated_scored = scored_population[:N_GENERATED_KEEP]
    generated_perms = [s["perm"] for s in generated_scored]

    generated_summary = pd.DataFrame([
        {
            "generated_id": i,
            "single_acc": s["accuracy"],
            "best_true_similarity": s["best_true_similarity"],
            "flip_similarity": s["flip_similarity"],
            "rot180_similarity": s["rot180_similarity"]
        }
        for i, s in enumerate(generated_scored)
    ])

    print()
    print("Top generated permutations:")
    print(generated_summary.to_string(index=False))

    random_background = make_random_perms(N_RANDOM_BACKGROUND, seed=seed + 2000)
    all_perms = generated_perms + random_background

    block_names = [f"generated_{i:02d}" for i in range(N_GENERATED_KEEP)] + [f"random_{i:02d}" for i in range(N_RANDOM_BACKGROUND)]
    block_type = ["generated"] * N_GENERATED_KEEP + ["random"] * N_RANDOM_BACKGROUND

    Phi_train = build_A_features(X_train, all_perms)
    Phi_test = build_A_features(X_test, all_perms)

    l1_model = fit_l1_model(Phi_train, y_train, C=C_l1)
    l1_pred = l1_model.predict(Phi_test)
    l1_acc = accuracy_score(y_test, l1_pred)

    importance = block_importance_from_pipeline(l1_model, n_blocks=TOTAL_BLOCKS, block_size=N_PIXELS)
    importance["name"] = block_names
    importance["type"] = block_type
    importance = importance.sort_values("importance_l1", ascending=False).reset_index(drop=True)
    importance["rank"] = np.arange(1, len(importance) + 1)

    top10 = importance.head(10)
    top20 = importance.head(20)

    generated_top10 = int((top10["type"] == "generated").sum())
    random_top10 = int((top10["type"] == "random").sum())
    generated_top20 = int((top20["type"] == "generated").sum())
    random_top20 = int((top20["type"] == "random").sum())

    generated_mean_rank = importance[importance["type"] == "generated"]["rank"].mean()
    random_mean_rank = importance[importance["type"] == "random"]["rank"].mean()
    generated_median_rank = importance[importance["type"] == "generated"]["rank"].median()
    random_median_rank = importance[importance["type"] == "random"]["rank"].median()

    print()
    print("======================================")
    print("FINAL RESULT")
    print("======================================")
    print()
    print(f"L1 C:                         {C_l1}")
    print(f"Feature dim:                  {Phi_train.shape[1]}")
    print(f"Evolution time:               {evolve_time:.2f} sec")
    print()
    print(f"Baseline x accuracy:          {baseline_acc:.4f}")
    print(f"True pair accuracy:           {true_pair_acc:.4f}")
    print(f"Random 99 accuracy:           {random_99_acc:.4f}")
    print(f"AR-v2 L1 accuracy:            {l1_acc:.4f}")
    print()
    print(f"Gain over baseline:           {l1_acc - baseline_acc:.4f}")
    print(f"Gain over random 99:          {l1_acc - random_99_acc:.4f}")
    print(f"Gap to true pair:             {true_pair_acc - l1_acc:.4f}")
    print()
    print("Selection:")
    print(f"Generated in Top10:           {generated_top10} / 10")
    print(f"Random in Top10:              {random_top10} / 10")
    print(f"Generated in Top20:           {generated_top20} / 20")
    print(f"Random in Top20:              {random_top20} / 20")
    print()
    print(f"Generated mean rank:          {generated_mean_rank:.2f}")
    print(f"Random mean rank:             {random_mean_rank:.2f}")
    print(f"Generated median rank:        {generated_median_rank:.2f}")
    print(f"Random median rank:           {random_median_rank:.2f}")
    print()
    print("Top 20 selected blocks:")
    print(importance.head(20)[["rank", "name", "type", "importance_l1", "nonzero_coeffs"]].to_string(index=False))

    print()
    print("Evolution history:")
    print(history.to_string(index=False))


if __name__ == "__main__":
    main()
