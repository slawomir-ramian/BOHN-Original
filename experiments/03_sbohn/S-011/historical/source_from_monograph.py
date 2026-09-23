import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


class SBOHNFeatureExtractor:
    def __init__(self, n_bits=6):
        self.n_bits = n_bits
        self.n_states = 2 ** n_bits
        self.perm_g = self._build_z3_permutation()
        self.perm_g2 = self.perm_g[self.perm_g]

    def _z3_permutation_index(self, i):
        bits = format(i, f"0{self.n_bits}b")
        new_bits = bits[2:4] + bits[4:6] + bits[0:2]
        return int(new_bits, 2)

    def _build_z3_permutation(self):
        return np.array([
            self._z3_permutation_index(i)
            for i in range(self.n_states)
        ])

    def transform(self, X):
        X = np.asarray(X)
        gX = X[:, self.perm_g]
        g2X = X[:, self.perm_g2]
        S3 = X + gX + g2X
        A1 = np.abs(X - gX)
        A2 = np.abs(X - g2X)
        return np.concatenate([S3, A1, A2], axis=1)


class SBOHNLR:
    def __init__(self, random_state=42, max_iter=5000):
        self.extractor = SBOHNFeatureExtractor()
        self.classifier = LogisticRegression(
            max_iter=max_iter,
            solver="liblinear",
            random_state=random_state
        )

    def fit(self, X, y):
        Phi = self.extractor.transform(X)
        self.classifier.fit(Phi, y)
        return self

    def predict(self, X):
        Phi = self.extractor.transform(X)
        return self.classifier.predict(Phi)

    def score(self, X, y):
        return accuracy_score(y, self.predict(X))


def make_reference_dataset(n_samples=800, noise=0.45, seed=0):
    rng = np.random.default_rng(seed)
    extractor = SBOHNFeatureExtractor()

    X = rng.normal(size=(n_samples, 64))

    gX = X[:, extractor.perm_g]
    g2X = X[:, extractor.perm_g2]

    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    S3 = X + gX + g2X

    idx_A1 = rng.choice(64, size=5, replace=False)
    idx_A2 = rng.choice(64, size=5, replace=False)
    idx_S3 = rng.choice(64, size=3, replace=False)

    w_A1 = rng.uniform(0.4, 1.3, size=5)
    w_A2 = rng.uniform(0.4, 1.3, size=5)
    w_S3 = rng.uniform(0.1, 0.5, size=3)

    signal = (
        A1[:, idx_A1] @ w_A1
        + A2[:, idx_A2] @ w_A2
        + S3[:, idx_S3] @ w_S3
    )

    threshold = np.median(signal)
    logits = signal - threshold + noise * rng.normal(size=n_samples)

    y = (logits > 0).astype(int)

    return X, y


def run_one(seed, n_samples=800, noise=0.45):
    X, y = make_reference_dataset(
        n_samples=n_samples, noise=noise, seed=seed
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=seed, stratify=y
    )

    baseline = LogisticRegression(
        max_iter=5000, solver="liblinear", random_state=seed
    )
    baseline.fit(X_train, y_train)
    baseline_acc = accuracy_score(y_test, baseline.predict(X_test))

    sbohn_lr = SBOHNLR(random_state=seed)
    sbohn_lr.fit(X_train, y_train)
    sbohn_acc = sbohn_lr.score(X_test, y_test)

    return baseline_acc, sbohn_acc


def main():
    seeds = range(100)

    baseline_scores = []
    sbohn_scores = []

    for seed in seeds:
        baseline_acc, sbohn_acc = run_one(seed)
        baseline_scores.append(baseline_acc)
        sbohn_scores.append(sbohn_acc)

    baseline_scores = np.array(baseline_scores)
    sbohn_scores = np.array(sbohn_scores)
    gains = sbohn_scores - baseline_scores

    print("===================================")
    print("SBOHN-LR multi-seed reference test")
    print("===================================")
    print()
    print(f"Number of seeds:       {len(list(seeds))}")
    print(f"Input dimension x:     64")
    print(f"SBOHN dimension Phi:   192")
    print()
    print("Accuracy:")
    print(f"Baseline LR on x:      "
          f"{baseline_scores.mean():.4f} +/- "
          f"{baseline_scores.std():.4f}")
    print(f"SBOHN-LR:              "
          f"{sbohn_scores.mean():.4f} +/- "
          f"{sbohn_scores.std():.4f}")
    print(f"Gain:                  "
          f"{gains.mean():.4f} +/- "
          f"{gains.std():.4f}")
    print()
    print("Robustness:")
    print(f"SBOHN better in:       "
          f"{np.sum(gains > 0)} / {len(gains)} seeds")
    print(f"SBOHN equal in:        "
          f"{np.sum(gains == 0)} / {len(gains)} seeds")
    print(f"SBOHN worse in:        "
          f"{np.sum(gains < 0)} / {len(gains)} seeds")
    print()
    print("Gain range:")
    print(f"Min gain:              {gains.min():.4f}")
    print(f"Max gain:              {gains.max():.4f}")


if __name__ == "__main__":
    main()
