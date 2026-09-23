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

def make_dataset(N=700, noise=0.35, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_perm(X, perm_g)
    g2X = apply_perm(X, perm_g2)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    asym_strength = (1.0 * A1[:, 7] + 0.8 * A1[:, 20]
                     + 0.7 * A2[:, 31] + 0.6 * A2[:, 42]
                     + 0.4 * A1[:, 5] * A2[:, 5])
    sym_signal = (0.3 * (X + gX + g2X)[:, 3]
                  + 0.2 * (X + gX + g2X)[:, 10])
    raw = asym_strength + sym_signal
    threshold = np.median(raw)
    logits = raw - threshold + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def feature_variants(X):
    gX = apply_perm(X, perm_g)
    g2X = apply_perm(X, perm_g2)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    sigma_3 = X + gX + g2X
    return {
        "x": X,
        "A1_abs_x_minus_gx": A1,
        "A2_abs_x_minus_g2x": A2,
        "A1_plus_A2": np.concatenate([A1, A2], axis=1),
        "x_plus_A1_A2": np.concatenate([X, A1, A2], axis=1),
        "sigma3_plus_A1_A2": np.concatenate([sigma_3, A1, A2], axis=1),
        "full_linear_Z3": np.concatenate([X, gX, g2X], axis=1),
    }

def evaluate_variant(X_feat, y, seed):
    X_train, X_test, y_train, y_test = train_test_split(
        X_feat, y, test_size=0.35, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=4000,
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
print("Z3 TEST: |x-g(x)| and |x-g^2(x)|")
print("======================================")
for name in names:
    scores = np.array([r[name] for r in all_results])
    print(f"{name:24s} mean={scores.mean():.4f}  "
          f"std={scores.std():.4f}")

print("\n======================================")
print("GAIN RELATIVE TO BASELINE x")
print("======================================")
baseline = np.array([r["x"] for r in all_results])
for name in names:
    if name == "x": continue
    scores = np.array([r[name] for r in all_results])
    gains = scores - baseline
    print(f"{name:24s} gain_mean={gains.mean():.4f}  "
          f"better={np.sum(gains > 0):2d}/50  "
          f"worse={np.sum(gains < 0):2d}/50")
