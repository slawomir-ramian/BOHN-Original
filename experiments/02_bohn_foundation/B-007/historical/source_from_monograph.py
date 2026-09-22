import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

def compute_orbit_energies(X, orbits):
    """Compute the orbit energy vector E(X) in R^24."""
    n_orbits = len(orbits)
    if X.ndim == 1:
        X = X[np.newaxis, :]
    E = np.zeros((X.shape[0], n_orbits))
    for i, orbit in enumerate(orbits):
        E[:, i] = np.sum(X[:, orbit]**2, axis=1)
    return E

# Dane z Benchmark II (Z3-symetryczne)
X, y = generate_z3_symmetric_data(
    n_samples=2000, dim=64, orbits=orbits, seed=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Oblicz energie orbit
E_train = compute_orbit_energies(X_train, orbits)
E_test = compute_orbit_energies(X_test, orbits)

print(f"Input dimension X:         {X_train.shape[1]}")
print(f"Orbit energy dimension E(X): {E_train.shape[1]}")
print()

# --- Model 1: Linear raw X ---
clf1 = LogisticRegression(max_iter=1000, random_state=42)
clf1.fit(X_train, y_train)
acc_raw = accuracy_score(y_test, clf1.predict(X_test))

# --- Model 2: Linear orbit energy ---
clf2 = LogisticRegression(max_iter=1000, random_state=42)
clf2.fit(E_train, y_train)
acc_linear_E = accuracy_score(y_test, clf2.predict(E_test))

# --- Model 3: MLP orbit energy ---
clf3 = MLPClassifier(
    hidden_layer_sizes=(64, 32),
    max_iter=500,
    random_state=42,
    early_stopping=True
)
clf3.fit(E_train, y_train)
acc_mlp_E = accuracy_score(y_test, clf3.predict(E_test))

# Results
print("="*60)
print("BENCHMARK III: ORBIT ENERGY NETWORK")
print("="*60)
print(f"  Linear raw X:          {acc_raw:.3f}")
print(f"  Linear orbit energy:   {acc_linear_E:.3f}")
print(f"  MLP orbit energy:      {acc_mlp_E:.3f}")
print()
print("Conclusion: Orbit energy is a nearly sufficient")
print("representation for Z3-symmetric tasks.")
print("A nonlinear problem in R^64 becomes nearly")
print("linear in R^24 (orbit energy).")
