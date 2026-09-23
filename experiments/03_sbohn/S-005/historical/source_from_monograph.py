import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def z3_permutation_index(i):
    bits = format(i, "06b")
    new_bits = bits[2:4] + bits[4:6] + bits[0:2]
    return int(new_bits, 2)

perm = np.array([z3_permutation_index(i) for i in range(64)])

def apply_g(X):
    return X[:, perm]

def make_dataset(N=700, noise=0.35, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_g(X)
    asym_strength = (
        1.2 * np.abs(X - gX)[:, 7]
        + 0.9 * np.abs(X - gX)[:, 20]
        + 0.7 * np.abs(X - gX)[:, 31]
        + 0.5 * np.abs(X - gX)[:, 42])
    sym_signal = 0.4 * (X + gX)[:, 3] + 0.3 * (X + gX)[:, 10]
    threshold = np.median(asym_strength + sym_signal)
    logits = asym_strength + sym_signal - threshold \
             + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def feature_variants(X):
    gX = apply_g(X)
    sigma = X + gX
    delta = X - gX
    abs_delta = np.abs(delta)
    return {
        "x": X,
        "x_plus_gx": sigma,
        "x_minus_gx": delta,
        "abs_x_minus_gx": abs_delta,
        "sigma_plus_abs_delta": np.concatenate([sigma, abs_delta], axis=1),
        "x_plus_abs_delta": np.concatenate([X, abs_delta], axis=1),
        "full_doublet": np.concatenate([sigma, delta], axis=1),
    }

def evaluate_variant(X_feat, y, seed):
    X_train, X_test, y_train, y_test = train_test_split(
        X_feat, y, test_size=0.35, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=3000,
                               solver="liblinear", random_state=seed)
    model.fit(X_train, y_train)
    return accuracy_score(y_test, model.predict(X_test))

seeds = range(50)
all_results = []
for seed in seeds:
    X, y = make_dataset(N=700, noise=0.35, seed=seed)
    variants = feature_variants(X)
    results = {n: evaluate_variant(f, y, seed)
               for n, f in variants.items()}
    all_results.append(results)

names = list(all_results[0].keys())
print("======================================")
print("FEATURE VARIANT COMPARISON BOHN/AOO")
print("======================================")
for name in names:
    scores = np.array([r[name] for r in all_results])
    print(f"{name:22s} mean={scores.mean():.4f}  "
          f"std={scores.std():.4f}")

print("\n======================================")
print("GAIN RELATIVE TO BASELINE x")
print("======================================")
baseline = np.array([r["x"] for r in all_results])
for name in names:
    if name == "x": continue
    scores = np.array([r[name] for r in all_results])
    gains = scores - baseline
    print(f"{name:22s} gain_mean={gains.mean():.4f}  "
          f"better={np.sum(gains > 0):2d}/50  "
          f"worse={np.sum(gains < 0):2d}/50")
