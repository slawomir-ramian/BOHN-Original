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

def asym_abs_features(X):
    return np.abs(X - apply_g(X))

def make_dataset(N=700, noise=0.35, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_g(X)
    asym_strength = (
        1.2 * np.abs(X - gX)[:, 7]
        + 0.9 * np.abs(X - gX)[:, 20]
        + 0.7 * np.abs(X - gX)[:, 31]
        + 0.5 * np.abs(X - gX)[:, 42]
    )
    threshold = np.median(asym_strength)
    logits = asym_strength - threshold + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def run_one(seed):
    X, y = make_dataset(N=700, noise=0.35, seed=seed)
    Xa = asym_abs_features(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=seed, stratify=y)
    Xa_train, Xa_test, ya_train, ya_test = train_test_split(
        Xa, y, test_size=0.35, random_state=seed, stratify=y)
    baseline = LogisticRegression(max_iter=2000,
                                  solver="liblinear", random_state=seed)
    asym_model = LogisticRegression(max_iter=2000,
                                    solver="liblinear", random_state=seed)
    baseline.fit(X_train, y_train)
    asym_model.fit(Xa_train, ya_train)
    return (accuracy_score(y_test, baseline.predict(X_test)),
            accuracy_score(ya_test, asym_model.predict(Xa_test)))

seeds = range(50)
baseline_scores, asym_scores = [], []
for seed in seeds:
    a, b = run_one(seed)
    baseline_scores.append(a)
    asym_scores.append(b)

baseline_scores = np.array(baseline_scores)
asym_scores = np.array(asym_scores)
gains = asym_scores - baseline_scores

print("======================================")
print("PURE TEST |x - g(x)|")
print("======================================")
print(f"Mean baseline on x:      {baseline_scores.mean():.4f}")
print(f"Mean |x-g(x)|:           {asym_scores.mean():.4f}")
print(f"Mean gain:               {gains.mean():.4f}")
print(f"|x-g(x)| better in {np.sum(gains > 0)} / {len(gains)} seeds")
print(f"|x-g(x)| worse in {np.sum(gains > 0)} / {len(gains)} seeds")
