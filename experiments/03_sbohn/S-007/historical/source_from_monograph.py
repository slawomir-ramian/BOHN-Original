import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def z3_permutation_index(i):
    bits = format(i, "06b")
    new_bits = bits[2:4] + bits[4:6] + bits[0:2]
    return int(new_bits, 2)

perm_g = np.array([z3_permutation_index(i) for i in range(64)])
perm_g2 = perm_g[perm_g]

def apply_perm(X, perm):
    return X[:, perm]

def make_dataset(N=800, noise=0.45, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_perm(X, perm_g)
    g2X = apply_perm(X, perm_g2)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    S3 = X + gX + g2X
    # Random coordinates and random weights in each seed
    idx_A1 = rng.choice(64, size=5, replace=False)
    idx_A2 = rng.choice(64, size=5, replace=False)
    idx_S3 = rng.choice(64, size=3, replace=False)
    w_A1 = rng.uniform(0.4, 1.3, size=5)
    w_A2 = rng.uniform(0.4, 1.3, size=5)
    w_S3 = rng.uniform(0.1, 0.5, size=3)
    asym_strength = A1[:, idx_A1] @ w_A1 + A2[:, idx_A2] @ w_A2
    sym_signal = S3[:, idx_S3] @ w_S3
    idx_cross = rng.choice(64, size=2, replace=False)
    cross_signal = 0.25 * A1[:, idx_cross[0]] * A2[:, idx_cross[1]]
    raw = asym_strength + sym_signal + cross_signal
    threshold = np.median(raw)
    logits = raw - threshold + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def feature_variants(X):
    gX = apply_perm(X, perm_g)
    g2X = apply_perm(X, perm_g2)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    S3 = X + gX + g2X
    return {
        "x": X,
        "full_linear_Z3": np.concatenate([X, gX, g2X], axis=1),
        "A1": A1,
        "A2": A2,
        "A1_A2": np.concatenate([A1, A2], axis=1),
        "x_A1_A2": np.concatenate([X, A1, A2], axis=1),
        "S3": S3,
        "S3_A1_A2": np.concatenate([S3, A1, A2], axis=1),
    }

def evaluate_variant(X_feat, y, seed):
    X_train, X_test, y_train, y_test = train_test_split(
        X_feat, y, test_size=0.35, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=5000,
                               solver="liblinear", random_state=seed)
    model.fit(X_train, y_train)
    return accuracy_score(y_test, model.predict(X_test))

seeds = range(100)
all_results = []
for seed in seeds:
    X, y = make_dataset(N=800, noise=0.45, seed=seed)
    variants = feature_variants(X)
    results = {n: evaluate_variant(f, y, seed)
               for n, f in variants.items()}
    all_results.append(results)

names = list(all_results[0].keys())
print("======================================")
print("RANDOM TEST: SBOHN / AOO")
print("======================================")
for name in names:
    scores = np.array([r[name] for r in all_results])
    print(f"{name:18s} mean={scores.mean():.4f}  "
          f"std={scores.std():.4f}")

print("\n======================================")
print("GAIN RELATIVE TO x")
print("======================================")
baseline = np.array([r["x"] for r in all_results])
for name in names:
    if name == "x": continue
    scores = np.array([r[name] for r in all_results])
    gains = scores - baseline
    print(f"{name:18s} gain_mean={gains.mean():.4f}  "
          f"better={np.sum(gains > 0):3d}/100  "
          f"worse={np.sum(gains < 0):3d}/100")
