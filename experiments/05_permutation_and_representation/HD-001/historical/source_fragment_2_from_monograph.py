import numpy as np
from sklearn.linear_model import SGDClassifier

def make_perm_z3(d):
    m = d // 3
    return np.concatenate([
        np.arange(m, 2*m),
        np.arange(2*m, 3*m),
        np.arange(0, m)
    ])

def generate_data(n, d, noise_std=0.1, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(n, d)
    perm_g = make_perm_z3(d)
    gX = X[:, perm_g]
    g2X = gX[:, perm_g]
    S3 = X + gX + g2X
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    w1, w2, w3 = rng.randn(d), rng.randn(d), rng.randn(d)
    signal = A1 @ w1 + A2 @ w2 + S3 @ w3
    eps = rng.randn(n) * noise_std
    y = (signal + eps > np.median(signal)).astype(int)
    return X, y, perm_g

def run_one(n, d, seed):
    X, y, perm_g = generate_data(n, d, seed=seed)
    split = int(0.7 * n)
    # Baseline
    clf = SGDClassifier(loss='log_loss', max_iter=500,
                        random_state=seed, tol=1e-3)
    clf.fit(X[:split], y[:split])
    raw_acc = clf.score(X[split:], y[split:])
    # SBOHN
    Xsb = sbohn_z3_features(X, perm_g)
    clf2 = SGDClassifier(loss='log_loss', max_iter=500,
                         random_state=seed, tol=1e-3)
    clf2.fit(Xsb[:split], y[:split])
    sb_acc = clf2.score(Xsb[split:], y[split:])
    return raw_acc, sb_acc

# --- Experiment 1: dimension scaling ---
print("Dimension scaling (n=2000, 10 seeds)")
for d in [63, 255, 1023, 4095]:
    raws, sbs = [], []
    for s in range(10):
        r, sb = run_one(2000, d, s)
        raws.append(r); sbs.append(sb)
    raws, sbs = np.array(raws), np.array(sbs)
    gain = (sbs - raws).mean()
    wins = int(np.sum(sbs > raws))
    print(f"d={d:5d}  base={raws.mean():.4f}  "
          f"sbohn={sbs.mean():.4f}  "
          f"gain={gain:.4f}  wins={wins}/10")

# --- Experiment 2: effect of n (d=4095) ---
print("\nEffect of n (d=4095, 10 seeds)")
for n in [2000, 5000, 10000]:
    raws, sbs = [], []
    for s in range(10):
        r, sb = run_one(n, 4095, s)
        raws.append(r); sbs.append(sb)
    raws, sbs = np.array(raws), np.array(sbs)
    gain = (sbs - raws).mean()
    wins = int(np.sum(sbs > raws))
    print(f"n={n:6d}  base={raws.mean():.4f}  "
          f"sbohn={sbs.mean():.4f}  "
          f"gain={gain:.4f}  wins={wins}/10")
