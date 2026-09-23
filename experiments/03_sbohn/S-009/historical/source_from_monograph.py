import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def z3_permutation_index(i):
    bits = format(i, "06b")
    new_bits = bits[2:4] + bits[4:6] + bits[0:2]
    return int(new_bits, 2)

perm_true_g = np.array([z3_permutation_index(i) for i in range(64)])

def apply_perm(X, perm):
    return X[:, perm]

def random_permutation(seed):
    return np.random.default_rng(seed).permutation(64)

def make_dataset(N=800, noise=0.45, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(N, 64))
    gX = apply_perm(X, perm_true_g)
    g2X = apply_perm(gX, perm_true_g)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    S3 = X + gX + g2X
    idx_A1 = rng.choice(64, size=5, replace=False)
    idx_A2 = rng.choice(64, size=5, replace=False)
    idx_S3 = rng.choice(64, size=3, replace=False)
    w_A1 = rng.uniform(0.4, 1.3, size=5)
    w_A2 = rng.uniform(0.4, 1.3, size=5)
    w_S3 = rng.uniform(0.1, 0.5, size=3)
    asym = A1[:, idx_A1] @ w_A1 + A2[:, idx_A2] @ w_A2
    sym = S3[:, idx_S3] @ w_S3
    raw = asym + sym
    threshold = np.median(raw)
    logits = raw - threshold + noise * rng.normal(size=N)
    y = (logits > 0).astype(int)
    return X, y

def sbohn_features(X, perm_g):
    gX = apply_perm(X, perm_g)
    g2X = apply_perm(gX, perm_g)
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    S3 = X + gX + g2X
    return np.concatenate([S3, A1, A2], axis=1)

def evaluate_features(X_feat, y, seed):
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_feat, y, test_size=0.35, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=4000,
                               solver="liblinear", random_state=seed)
    model.fit(X_tr, y_tr)
    return accuracy_score(y_te, model.predict(X_te))

def run_one(seed, n_random_perms=50):
    X, y = make_dataset(N=800, noise=0.45, seed=seed)
    acc_x = evaluate_features(X, y, seed)
    X_true = sbohn_features(X, perm_true_g)
    acc_true = evaluate_features(X_true, y, seed)
    random_scores = []
    for k in range(n_random_perms):
        perm = random_permutation(seed * 1000 + k)
        X_rand = sbohn_features(X, perm)
        acc_rand = evaluate_features(X_rand, y, seed)
        random_scores.append(acc_rand)
    random_scores = np.array(random_scores)
    rank_true = 1 + np.sum(random_scores > acc_true)
    return {
        "acc_x": acc_x, "acc_true": acc_true,
        "rand_mean": random_scores.mean(),
        "rand_max": random_scores.max(),
        "rank_true": rank_true,
        "true_beats_all": acc_true > random_scores.max()
    }

seeds = range(30)
results = [run_one(seed, n_random_perms=50) for seed in seeds]

acc_x = np.array([r["acc_x"] for r in results])
acc_true = np.array([r["acc_true"] for r in results])
rand_mean = np.array([r["rand_mean"] for r in results])
rand_max = np.array([r["rand_max"] for r in results])
rank_true = np.array([r["rank_true"] for r in results])
true_beats_all = np.array([r["true_beats_all"] for r in results])

print("======================================")
print("TEST: HIDDEN SYMMETRY DETECTION")
print("======================================")
print(f"Baseline x mean:          {acc_x.mean():.4f}")
print(f"SBOHN true mean:          {acc_true.mean():.4f}")
print(f"Random SBOHN mean:        {rand_mean.mean():.4f}")
print(f"Best random SBOHN mean:   {rand_max.mean():.4f}")
print()
print(f"True gain over x:         "
      f"{(acc_true - acc_x).mean():.4f}")
print(f"True gain over rand mean: "
      f"{(acc_true - rand_mean).mean():.4f}")
print(f"True gain over rand max:  "
      f"{(acc_true - rand_max).mean():.4f}")
print()
print(f"True symmetry best in:    "
      f"{np.sum(true_beats_all)} / {len(seeds)} runs")
print(f"Average true rank:        "
      f"{rank_true.mean():.2f} / 51")
print()
print("Ranks true symmetry:")
print(rank_true)
