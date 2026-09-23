import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

def z3_permutation_index(i):
    bits = format(i, "06b")
    new_bits = bits[2:4] + bits[4:6] + bits[0:2]
    return int(new_bits, 2)

perm = np.array([z3_permutation_index(i) for i in range(64)])

def apply_g(X):
    return X[:, perm]

def make_dataset(N=500, noise=0.8, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_g(X)
    sym = 1.0 * (X + gX)[:, 3] + 0.7 * (X + gX)[:, 10]
    asym = 1.0 * (X - gX)[:, 7] - 0.7 * (X - gX)[:, 20]
    logits = sym + asym + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def doublet_features(X):
    gX = apply_g(X)
    return np.concatenate([X + gX, X - gX], axis=1)

def run_one(seed):
    X, y = make_dataset(N=500, noise=0.8, seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=seed, stratify=y)
    baseline = MLPClassifier(hidden_layer_sizes=(16,),
                             activation="relu", max_iter=800,
                             random_state=seed)
    baseline.fit(X_train, y_train)
    acc_base = accuracy_score(y_test, baseline.predict(X_test))

    Xd = doublet_features(X)
    Xd_train, Xd_test, yd_train, yd_test = train_test_split(
        Xd, y, test_size=0.35, random_state=seed, stratify=y)
    doublet = MLPClassifier(hidden_layer_sizes=(16,),
                            activation="relu", max_iter=800,
                            random_state=seed)
    doublet.fit(Xd_train, yd_train)
    acc_doublet = accuracy_score(yd_test, doublet.predict(Xd_test))
    return acc_base, acc_doublet

seeds = range(20)
baseline_scores = []
doublet_scores = []
for seed in seeds:
    acc_base, acc_doublet = run_one(seed)
    baseline_scores.append(acc_base)
    doublet_scores.append(acc_doublet)

baseline_scores = np.array(baseline_scores)
doublet_scores = np.array(doublet_scores)
gains = doublet_scores - baseline_scores

print("======================================")
print("DOUBLET TEST RESULTS")
print("======================================")
print(f"Mean baseline: {baseline_scores.mean():.4f}")
print(f"Mean doublet:  {doublet_scores.mean():.4f}")
print(f"Mean gain:     {gains.mean():.4f}")
print(f"Median gain:   {np.median(gains):.4f}")
print(f"Doublet better in {np.sum(gains > 0)} / {len(gains)} seeds")
print(f"Doublet worse in {np.sum(gains < 0)} / {len(gains)} seeds")
