"""
Adaptive BOHN Soft Router -- test on the Iris dataset (binary: classes 0 vs 1)
"""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

# === Z3 Orbits ===
def compute_z3_orbits(dim=64):
    n_bits = 6
    def z3_permute(index):
        bits = format(index, f'0{n_bits}b')
        shifted = bits[2:] + bits[:2]
        return int(shifted, 2)
    visited = set()
    orbits = []
    for i in range(dim):
        if i not in visited:
            orbit = []
            current = i
            for _ in range(3):
                orbit.append(current)
                visited.add(current)
                current = z3_permute(current)
            orbits.append(sorted(set(orbit)))
    return orbits

# === Orbit histogram ===
def compute_orbit_histogram(X, orbits):
    n_samples = X.shape[0]
    features = []
    for orb in orbits:
        Xs = X[:, orb]
        E = np.sum(Xs**2, axis=1)
        M = np.mean(Xs, axis=1)
        A = np.mean(np.abs(Xs), axis=1)
        features.extend([E, M, A])
    return np.column_stack(features)

# === Adaptive BOHN Router ===
class AdaptiveBOHNRouter:
    def __init__(self, input_dim=4, target_dim=64):
        self.input_dim = input_dim
        self.target_dim = target_dim
        self.orbits = compute_z3_orbits(target_dim)
        self.router_weights = np.random.randn(input_dim, target_dim) * 0.1

    def _get_permutation_matrix(self):
        exp_w = np.exp(self.router_weights
                       - np.max(self.router_weights, axis=0, keepdims=True))
        return exp_w / np.sum(exp_w, axis=0, keepdims=True)

    def forward(self, X_raw):
        P = self._get_permutation_matrix()
        X_mapped = X_raw @ P
        Phi = compute_orbit_histogram(X_mapped, self.orbits)
        return Phi, X_mapped, P

    def fit_fisher(self, X_train, y_train, steps=300, sigma=0.05):
        """Optimization of Fisher criterion using evolutionary algorithm."""
        def fisher_score(Phi, y):
            classes = np.unique(y)
            grand_mean = np.mean(Phi, axis=0)
            between = 0
            within = 0
            for c in classes:
                mask = y == c
                class_phi = Phi[mask]
                n_c = class_phi.shape[0]
                class_mean = np.mean(class_phi, axis=0)
                between += n_c * np.sum((class_mean - grand_mean)**2)
                within += np.sum(np.var(class_phi, axis=0)) * n_c
            return between / (within + 1e-10)

        best_weights = self.router_weights.copy()
        self.router_weights = best_weights
        Phi, _, _ = self.forward(X_train)
        best_score = fisher_score(Phi, y_train)
        for step in range(steps):
            noise = np.random.randn(*self.router_weights.shape) * sigma
            trial_weights = best_weights + noise
            self.router_weights = trial_weights
            Phi, _, _ = self.forward(X_train)
            score = fisher_score(Phi, y_train)
            if score > best_score:
                best_score = score
                best_weights = trial_weights.copy()
        self.router_weights = best_weights
        return best_score

# === Experiment ===
iris = load_iris()
mask = iris.target < 2
X_all = iris.data[mask]
y_all = iris.target[mask]

seeds = [0, 1, 2, 3, 4, 5, 42, 123, 999]
results_raw, results_random, results_optimized = [], [], []

print("=" * 70)
print("ADAPTIVE BOHN SOFT ROUTER - BINARY IRIS (classes 0 vs 1)")
print("=" * 70)

for seed in seeds:
    np.random.seed(seed)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_all, y_all, test_size=0.3, random_state=seed, stratify=y_all)
    sc = StandardScaler()
    X_tr_s = sc.fit_transform(X_tr)
    X_te_s = sc.transform(X_te)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_tr_s, y_tr)
    acc_raw = accuracy_score(y_te, clf.predict(X_te_s))
    results_raw.append(acc_raw)

    router_r = AdaptiveBOHNRouter(4, 64)
    Phi_tr_r, _, _ = router_r.forward(X_tr_s)
    Phi_te_r, _, _ = router_r.forward(X_te_s)
    clf_r = LogisticRegression(max_iter=1000)
    clf_r.fit(Phi_tr_r, y_tr)
    acc_rand = accuracy_score(y_te, clf_r.predict(Phi_te_r))
    results_random.append(acc_rand)

    router_o = AdaptiveBOHNRouter(4, 64)
    fisher = router_o.fit_fisher(X_tr_s, y_tr, steps=300, sigma=0.05)
    Phi_tr_o, _, _ = router_o.forward(X_tr_s)
    Phi_te_o, _, _ = router_o.forward(X_te_s)
    clf_o = LogisticRegression(max_iter=1000)
    clf_o.fit(Phi_tr_o, y_tr)
    acc_opt = accuracy_score(y_te, clf_o.predict(Phi_te_o))
    results_optimized.append(acc_opt)

    print(f"Seed {seed:>3d}: raw={acc_raw:.4f}  "
          f"random={acc_rand:.4f}  optimized={acc_opt:.4f}  "
          f"Fisher={fisher:.4f}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Raw Iris baseline:       mean={np.mean(results_raw):.4f} "
      f"+/- {np.std(results_raw):.4f}")
print(f"BOHN random routing:     mean={np.mean(results_random):.4f} "
      f"+/- {np.std(results_random):.4f}")
print(f"BOHN optimized (Fisher): mean={np.mean(results_optimized):.4f} "
      f"+/- {np.std(results_optimized):.4f}")
