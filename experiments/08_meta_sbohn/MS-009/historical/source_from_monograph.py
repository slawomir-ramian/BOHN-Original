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
SEEDS = list(range(20))
TASKS = ["easy", "medium", "hard"]
POPULATION_SIZE = 60
GENERATIONS = 25
ELITE_SIZE = 6
LAMBDA_FIXED = 0.05
LAMBDA_START = 0.12

# ---------------- image transforms ----------------
def reshape_images(X):
    return X.reshape(-1, IMAGE_SIZE, IMAGE_SIZE)

def flatten_images(X):
    return X.reshape(X.shape[0], -1)

def flip_horizontal_transform(X):
    return flatten_images(reshape_images(X)[:, :, ::-1])

def rotate_180_transform(X):
    return flatten_images(np.rot90(reshape_images(X), k=2, axes=(1, 2)))

def rotate_90_transform(X):
    return flatten_images(np.rot90(reshape_images(X), k=1, axes=(1, 2)))

def transform_to_perm(transform_fn):
    idx = np.arange(N_PIXELS).reshape(1, N_PIXELS).astype(float)
    return transform_fn(idx).astype(int).reshape(-1)

TRUE_FLIP = transform_to_perm(flip_horizontal_transform)
TRUE_ROT180 = transform_to_perm(rotate_180_transform)
TRUE_ROT90 = transform_to_perm(rotate_90_transform)

# ---------------- task generation ----------------
def make_labels_for_task(X, task="medium", seed=0, noise=0.10):
    rng = np.random.default_rng(seed)
    parts = []

    XF = flip_horizontal_transform(X)
    AF = np.abs(X - XF)
    idx = rng.choice(N_PIXELS, size=10, replace=False)
    w = rng.uniform(0.5, 1.5, size=10)
    parts.append(AF[:, idx] @ w)

    if task in ["medium", "hard"]:
        XR = rotate_180_transform(X)
        AR = np.abs(X - XR)
        idx = rng.choice(N_PIXELS, size=10, replace=False)
        w = rng.uniform(0.5, 1.5, size=10)
        parts.append(AR[:, idx] @ w)

    if task == "hard":
        X90 = rotate_90_transform(X)
        A90 = np.abs(X - X90)
        idx = rng.choice(N_PIXELS, size=10, replace=False)
        w = rng.uniform(0.5, 1.5, size=10)
        parts.append(A90[:, idx] @ w)

    signal = np.sum(parts, axis=0)
    signal += noise * rng.normal(size=len(X))
    return (signal > np.median(signal)).astype(int)

# ---------------- SBOHN features ----------------
def apply_perm(X, perm):
    return X[:, perm]

def A_features(X, perm):
    return np.abs(X - apply_perm(X, perm))

def build_A_features(X, perms):
    return np.concatenate([A_features(X, p) for p in perms], axis=1)

def perm_similarity(p, q):
    return np.mean(p == q)

def true_similarity_for_task(perm, task):
    sim_flip = perm_similarity(perm, TRUE_FLIP)
    sim_rot180 = perm_similarity(perm, TRUE_ROT180)
    sim_rot90 = perm_similarity(perm, TRUE_ROT90)
    if task == "easy":
        best = sim_flip
    elif task == "medium":
        best = max(sim_flip, sim_rot180)
    elif task == "hard":
        best = max(sim_flip, sim_rot180, sim_rot90)
    else:
        raise ValueError("Unknown task")
    return dict(sim_flip=sim_flip, sim_rot180=sim_rot180,
                sim_rot90=sim_rot90, best_task_sim=best)

# ---------------- classifier ----------------
def make_lr():
    return make_pipeline(StandardScaler(),
                         LogisticRegression(max_iter=3000, solver="lbfgs"))

def evaluate_features(X_train, X_test, y_train, y_test):
    model = make_lr()
    model.fit(X_train, y_train)
    return accuracy_score(y_test, model.predict(X_test))

def evaluate_perm(X_train, X_test, y_train, y_test, perm):
    return evaluate_features(A_features(X_train, perm),
                             A_features(X_test, perm),
                             y_train, y_test)

def evaluate_perm_set(X_train, X_test, y_train, y_test, perms):
    return evaluate_features(build_A_features(X_train, perms),
                             build_A_features(X_test, perms),
                             y_train, y_test)

# ---------------- geometry generator ----------------
def pixel_coordinates():
    rows, cols = [], []
    for r in range(IMAGE_SIZE):
        for c in range(IMAGE_SIZE):
            rows.append(r)
            cols.append(c)
    r = np.array(rows, dtype=float)
    c = np.array(cols, dtype=float)
    r = 2.0 * (r / (IMAGE_SIZE - 1)) - 1.0
    c = 2.0 * (c / (IMAGE_SIZE - 1)) - 1.0
    return r, c

PIX_R, PIX_C = pixel_coordinates()
PIX_COORDS = np.column_stack([PIX_R, PIX_C])

def geometry_features_v2():
    r, c = PIX_R, PIX_C
    return np.column_stack([
        np.ones_like(r), r, c, r**2, c**2, r*c, r**3, c**3,
        np.sin(np.pi*r), np.sin(np.pi*c),
        np.cos(np.pi*r), np.cos(np.pi*c),
        np.sin(np.pi*(r+c)), np.cos(np.pi*(r-c)),
    ])

GEOM_V2 = geometry_features_v2()
N_THETA = GEOM_V2.shape[1]

def theta_to_perm(theta):
    score = GEOM_V2 @ theta
    jitter = 1e-9 * np.arange(len(score))
    return np.argsort(score + jitter)

# ---------------- unsupervised geometry score ----------------
def neighbor_pairs():
    pairs = []
    for r in range(IMAGE_SIZE):
        for c in range(IMAGE_SIZE):
            i = r * IMAGE_SIZE + c
            if r + 1 < IMAGE_SIZE:
                pairs.append((i, (r + 1) * IMAGE_SIZE + c))
            if c + 1 < IMAGE_SIZE:
                pairs.append((i, r * IMAGE_SIZE + c + 1))
    return pairs

NEIGHBOR_PAIRS = neighbor_pairs()

def geometry_smoothness_score(perm):
    dists = []
    for i, j in NEIGHBOR_PAIRS:
        dists.append(np.linalg.norm(PIX_COORDS[perm[i]] - PIX_COORDS[perm[j]]))
    return float(1.0 - np.mean(dists) / np.sqrt(8.0))

def displacement_consistency_score(perm):
    target_coords = PIX_COORDS[perm]
    displacement = target_coords - PIX_COORDS
    diffs = []
    for i, j in NEIGHBOR_PAIRS:
        diffs.append(np.linalg.norm(displacement[i] - displacement[j]))
    return float(1.0 - np.mean(diffs) / np.sqrt(8.0))

def geometry_score(perm):
    return 0.5 * geometry_smoothness_score(perm) + \
           0.5 * displacement_consistency_score(perm)

# ---------------- theta evaluation ----------------
def evaluate_theta(X_train, X_test, y_train, y_test, theta, task, lambda_geometry=0.0):
    perm = theta_to_perm(theta)
    acc = evaluate_perm(X_train, X_test, y_train, y_test, perm)
    geo = geometry_score(perm)
    sims = true_similarity_for_task(perm, task)
    return dict(theta=theta, perm=perm, accuracy=acc, geometry_score=geo,
                fitness=acc + lambda_geometry * geo, **sims)

# ---------------- evolution ----------------
def mutate_theta(theta, rng, sigma=0.25):
    return theta + sigma * rng.normal(size=theta.shape)

def crossover_theta(theta1, theta2, rng):
    alpha = rng.uniform(0.0, 1.0)
    return alpha * theta1 + (1.0 - alpha) * theta2

def lambda_schedule(mode, gen, generations):
    if mode == "accuracy_only":
        return 0.0
    if mode == "fixed_geometry":
        return LAMBDA_FIXED
    if mode == "annealed_geometry":
        frac = 1.0 - gen / max(1, generations - 1)
        return LAMBDA_START * frac
    raise ValueError("Unknown mode")

def evolve_geometry_generator(X_train, X_test, y_train, y_test, task, mode,
                              population_size=60, generations=25,
                              elite_size=6, mutation_sigma=0.25,
                              seed=0):
    rng = np.random.default_rng(seed)
    population = [rng.normal(scale=1.0, size=N_THETA)
                  for _ in range(population_size)]
    best_by_accuracy = None
    history = []

    for gen in range(generations):
        lambda_t = lambda_schedule(mode, gen, generations)
        scored = [evaluate_theta(X_train, X_test, y_train, y_test,
                                 theta, task, lambda_t)
                  for theta in population]
        scored_by_fitness = sorted(scored, key=lambda d: d["fitness"], reverse=True)
        scored_by_accuracy = sorted(scored, key=lambda d: d["accuracy"], reverse=True)

        if best_by_accuracy is None or \
           scored_by_accuracy[0]["accuracy"] > best_by_accuracy["accuracy"]:
            best_by_accuracy = scored_by_accuracy[0]

        history.append(dict(
            generation=gen,
            lambda_t=lambda_t,
            best_accuracy=scored_by_accuracy[0]["accuracy"],
            global_best_accuracy=best_by_accuracy["accuracy"],
            mean_accuracy=float(np.mean([s["accuracy"] for s in scored])),
            mean_geometry=float(np.mean([s["geometry_score"] for s in scored])),
            best_geometry=best_by_accuracy["geometry_score"],
            best_task_sim=best_by_accuracy["best_task_sim"],
        ))

        elites = [s["theta"] for s in scored_by_fitness[:elite_size]]
        new_population = elites.copy()
        while len(new_population) < population_size:
            if rng.random() < 0.6:
                parent = elites[rng.integers(0, elite_size)]
                child = mutate_theta(parent, rng, sigma=mutation_sigma)
            else:
                t1 = elites[rng.integers(0, elite_size)]
                t2 = elites[rng.integers(0, elite_size)]
                child = crossover_theta(t1, t2, rng)
                child = mutate_theta(child, rng, sigma=mutation_sigma)
            new_population.append(child)
        population = new_population
        mutation_sigma *= 0.97

    return best_by_accuracy, pd.DataFrame(history)

# ---------------- experiment runner ----------------
def make_task_data(seed, task):
    digits = load_digits()
    X = digits.data.astype(np.float32) / 16.0
    y = make_labels_for_task(X, task=task, seed=seed, noise=0.10)
    return train_test_split(X, y, test_size=0.30,
                            random_state=seed, stratify=y)

def true_perms_for_task(task):
    if task == "easy": return [TRUE_FLIP]
    if task == "medium": return [TRUE_FLIP, TRUE_ROT180]
    if task == "hard": return [TRUE_FLIP, TRUE_ROT180, TRUE_ROT90]
    raise ValueError("Unknown task")

def stable_seed(seed, mode, task):
    mode_offset = {"accuracy_only": 10000,
                   "fixed_geometry": 20000,
                   "annealed_geometry": 30000}[mode]
    task_offset = {"easy": 1000, "medium": 2000, "hard": 3000}[task]
    return seed + mode_offset + task_offset

def basin_flags(final_acc, best_sim, geo_score):
    return dict(
        acc_ge_090=final_acc >= 0.90,
        acc_ge_092=final_acc >= 0.92,
        acc_ge_094=final_acc >= 0.94,
        sim_ge_025=best_sim >= 0.25,
        sim_ge_050=best_sim >= 0.50,
        geo_ge_060=geo_score >= 0.60,
        geo_ge_070=geo_score >= 0.70,
        acc092_and_sim025=(final_acc >= 0.92 and best_sim >= 0.25),
        acc092_and_geo070=(final_acc >= 0.92 and geo_score >= 0.70),
    )

def run_one(seed, task, mode):
    X_train, X_test, y_train, y_test = make_task_data(seed, task)
    baseline_acc = evaluate_features(X_train, X_test, y_train, y_test)
    true_acc = evaluate_perm_set(X_train, X_test, y_train, y_test,
                                 true_perms_for_task(task))
    best, history = evolve_geometry_generator(
        X_train, X_test, y_train, y_test, task=task, mode=mode,
        population_size=POPULATION_SIZE, generations=GENERATIONS,
        elite_size=ELITE_SIZE, mutation_sigma=0.25,
        seed=stable_seed(seed, mode, task))
    row = dict(seed=seed, task=task, mode=mode,
               baseline_acc=baseline_acc,
               true_acc=true_acc,
               final_acc=best["accuracy"],
               gain_over_baseline=best["accuracy"] - baseline_acc,
               gap_to_true=true_acc - best["accuracy"],
               best_task_sim=best["best_task_sim"],
               geometry_score=best["geometry_score"],
               auc=float(history["global_best_accuracy"].mean()))
    row.update(basin_flags(best["accuracy"],
                           best["best_task_sim"],
                           best["geometry_score"]))
    return row

if __name__ == "__main__":
    modes = ["accuracy_only", "fixed_geometry", "annealed_geometry"]
    rows = []
    for seed in SEEDS:
        for task in TASKS:
            for mode in modes:
                print(f"{mode} | seed={seed} | task={task}")
                rows.append(run_one(seed, task, mode))
    df = pd.DataFrame(rows)
    print(df.groupby(["mode", "task"])[["final_acc", "best_task_sim",
                                        "geometry_score", "auc"]].mean())
    print(df.groupby(["mode", "task"])[["acc_ge_092", "sim_ge_025",
                                        "acc092_and_sim025"]].mean())
