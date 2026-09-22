"""Adapter wykonawczy B-001--B-009.

Algorytmy zachowują logikę listingów z monografii. Oryginały 1:1 znajdują się
w ``experiments/02_bohn_foundation/B-*/historical``. Ten moduł usuwa wyłącznie
zależność od kolejności komórek/listingów, aby testy mogły importować funkcje.
"""

from __future__ import annotations

from collections import defaultdict  # zachowane jak w Listing A.1

import numpy as np


def z3_permutation(state_index, n_bits=6):
    """Cyclic shift of two-bit blocks."""
    bits = format(state_index, f"0{n_bits}b")
    block1 = bits[0:2]
    block2 = bits[2:4]
    block3 = bits[4:6]
    new_bits = block2 + block3 + block1
    return int(new_bits, 2)


def compute_z3_orbits(n_states=64, n_bits=6):
    """Compute all orbits of the Z3 action on the set of states."""
    visited = set()
    orbits = []
    for state in range(n_states):
        if state in visited:
            continue
        orbit = set()
        current = state
        for _ in range(3):
            orbit.add(current)
            current = z3_permutation(current, n_bits)
        orbits.append(sorted(orbit))
        visited.update(orbit)
    return orbits


def compute_orbit_histogram(X, orbits):
    """Compute the orbit histogram Phi(X) in R^72."""
    single = X.ndim == 1
    if single:
        X = X[np.newaxis, :]
    batch_size = X.shape[0]
    n_orbits = len(orbits)
    energy = np.zeros((batch_size, n_orbits))
    mean = np.zeros((batch_size, n_orbits))
    amplitude = np.zeros((batch_size, n_orbits))
    for index, orbit in enumerate(orbits):
        orbit_idx = np.array(orbit)
        X_orbit = X[:, orbit_idx]
        energy[:, index] = np.sum(X_orbit**2, axis=1)
        mean[:, index] = np.mean(X_orbit, axis=1)
        amplitude[:, index] = np.mean(np.abs(X_orbit), axis=1)
    phi = np.concatenate([energy, mean, amplitude], axis=1)
    return phi[0] if single else phi


class ReversibleRMIGLayer:
    """Reversible permutation-sign RMIG layer from Listing A.3."""

    def __init__(self, n_states=64, n_bits=6, seed=42):
        self.n_states = n_states
        self.n_bits = n_bits
        self.perm = np.array(
            [z3_permutation(state, n_bits) for state in range(n_states)]
        )
        self.inv_perm = np.zeros(n_states, dtype=int)
        for index, permuted in enumerate(self.perm):
            self.inv_perm[permuted] = index
        rng = np.random.RandomState(seed)
        self.weights = rng.choice([-1.0, 1.0], size=n_states)

    def forward(self, X):
        self._input = X.copy()
        X_permuted = X[..., self.perm]
        return self.weights * X_permuted

    def inverse(self, Y):
        X_permuted = self.weights * Y
        return X_permuted[..., self.inv_perm]

    def backward(self, grad_Y):
        grad_X_permuted = self.weights * grad_Y
        grad_X = grad_X_permuted[..., self.inv_perm]
        X_permuted = self._input[..., self.perm]
        grad_W = X_permuted * grad_Y
        return grad_X, grad_W

    def set_weights(self, new_weights):
        self.weights = new_weights.copy()


def test_reversibility(layer, n_tests=100, dim=64):
    max_error = 0.0
    for _ in range(n_tests):
        X = np.random.randn(dim)
        X_rec = layer.inverse(layer.forward(X))
        max_error = max(max_error, np.max(np.abs(X - X_rec)))
    return max_error


def test_gradient_input(layer, dim=64, eps=1e-5):
    X = np.random.randn(dim)
    layer.forward(X)
    grad_Y = np.random.randn(dim)
    grad_X_analytic, _ = layer.backward(grad_Y)
    grad_X_numeric = np.zeros(dim)
    for index in range(dim):
        X_plus = X.copy()
        X_plus[index] += eps
        Y_plus = layer.forward(X_plus)
        X_minus = X.copy()
        X_minus[index] -= eps
        Y_minus = layer.forward(X_minus)
        grad_X_numeric[index] = np.sum(grad_Y * (Y_plus - Y_minus) / (2 * eps))
    error = np.max(np.abs(grad_X_analytic - grad_X_numeric))
    return error, grad_X_analytic, grad_X_numeric


def test_gradient_weights(layer, dim=64, eps=1e-5):
    X = np.random.randn(dim)
    layer.forward(X)
    grad_Y = np.random.randn(dim)
    _, grad_W_analytic = layer.backward(grad_Y)
    grad_W_numeric = np.zeros(dim)
    original_weights = layer.weights.copy()
    for index in range(dim):
        w_plus = original_weights.copy()
        w_plus[index] += eps
        layer.set_weights(w_plus)
        Y_plus = layer.forward(X)
        w_minus = original_weights.copy()
        w_minus[index] -= eps
        layer.set_weights(w_minus)
        Y_minus = layer.forward(X)
        grad_W_numeric[index] = np.sum(grad_Y * (Y_plus - Y_minus) / (2 * eps))
    layer.set_weights(original_weights)
    error = np.max(np.abs(grad_W_analytic - grad_W_numeric))
    return error, grad_W_analytic, grad_W_numeric


def generate_linear_data(n_samples=2000, dim=64, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, dim)
    w_true = rng.randn(dim)
    y = (X @ w_true > 0).astype(int)
    return X, y


def apply_z3_action(X, perm):
    return X[:, perm]


def generate_z3_symmetric_data(n_samples=2000, dim=64, orbits=None, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, dim)
    E_even = np.zeros(n_samples)
    E_odd = np.zeros(n_samples)
    for index, orbit in enumerate(orbits):
        orbit_energy = np.sum(X[:, orbit] ** 2, axis=1)
        if index % 2 == 0:
            E_even += orbit_energy
        else:
            E_odd += orbit_energy
    y = (E_even > E_odd).astype(int)
    return X, y


def compute_orbit_energies(X, orbits):
    if X.ndim == 1:
        X = X[np.newaxis, :]
    energy = np.zeros((X.shape[0], len(orbits)))
    for index, orbit in enumerate(orbits):
        energy[:, index] = np.sum(X[:, orbit] ** 2, axis=1)
    return energy


def generate_z3_data_rich(n_samples=2000, dim=64, orbits=None, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, dim)
    score = np.zeros(n_samples)
    for index, orbit in enumerate(orbits):
        X_orbit = X[:, orbit]
        E_i = np.sum(X_orbit**2, axis=1)
        M_i = np.mean(X_orbit, axis=1)
        A_i = np.mean(np.abs(X_orbit), axis=1)
        if index % 3 == 0:
            score += E_i
        elif index % 3 == 1:
            score += M_i**2
        else:
            score += A_i
    y = (score > np.median(score)).astype(int)
    return X, y


def test_invariance_single(orbits, dim=64, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(dim)
    perm = np.array([z3_permutation(state) for state in range(dim)])
    perm2 = perm[perm]
    Phi_e = compute_orbit_histogram(X, orbits)
    Phi_g = compute_orbit_histogram(X[perm], orbits)
    Phi_g2 = compute_orbit_histogram(X[perm2], orbits)
    err_g = np.max(np.abs(Phi_e - Phi_g))
    err_g2 = np.max(np.abs(Phi_e - Phi_g2))
    return err_g, err_g2, Phi_e, Phi_g, Phi_g2


def test_invariance_batch(orbits, n_samples=100, dim=64, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, dim)
    perm = np.array([z3_permutation(state) for state in range(dim)])
    perm2 = perm[perm]
    Phi_e = compute_orbit_histogram(X, orbits)
    Phi_g = compute_orbit_histogram(X[:, perm], orbits)
    Phi_g2 = compute_orbit_histogram(X[:, perm2], orbits)
    err_g = np.max(np.abs(Phi_e - Phi_g))
    err_g2 = np.max(np.abs(Phi_e - Phi_g2))
    return max(err_g, err_g2), err_g, err_g2
