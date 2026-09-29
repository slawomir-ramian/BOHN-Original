"""Jawne prymitywy końcowego suite'u RMIG/Meta-FBOHN.

Kod historyczny pozostaje osobno w katalogach eksperymentów. Ten moduł służy
do szybkich testów kontraktów strukturalnych bez uruchamiania ewolucji.
"""
from __future__ import annotations

import numpy as np

EPS = 1e-6
N_NODES = 18
ORBIT_SIZE = 3
N_ORBITS = 6


def rmig_orbits() -> list[list[int]]:
    return [[3 * index, 3 * index + 1, 3 * index + 2] for index in range(N_ORBITS)]


ORBITS = rmig_orbits()


def z3_permutation(k: int = 1) -> np.ndarray:
    permutation = np.arange(N_NODES)
    for orbit in ORBITS:
        for index, node in enumerate(orbit):
            permutation[node] = orbit[(index + k) % ORBIT_SIZE]
    return permutation


def build_rmig_edges() -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for a, b, c in ORBITS:
        for left, right in [(a, b), (b, c), (c, a)]:
            edges.add(tuple(sorted((left, right))))
    for orbit_index in range(N_ORBITS - 1):
        for index in range(ORBIT_SIZE):
            edges.add(tuple(sorted((ORBITS[orbit_index][index], ORBITS[orbit_index + 1][index]))))
    for first, second, shift in [(0, 2, 1), (1, 3, 2), (2, 4, 1), (3, 5, 2),
                                 (0, 3, 2), (1, 4, 1), (2, 5, 2)]:
        for index in range(ORBIT_SIZE):
            edges.add(tuple(sorted((ORBITS[first][index], ORBITS[second][(index + shift) % ORBIT_SIZE]))))
    return sorted(edges)


EDGES = build_rmig_edges()


def adjacency_matrix() -> np.ndarray:
    adjacency = np.zeros((N_NODES, N_NODES), dtype=float)
    for left, right in EDGES:
        adjacency[left, right] = adjacency[right, left] = 1.0
    return adjacency


ADJ = adjacency_matrix()
LAPLACIAN = np.diag(ADJ.sum(axis=1)) - ADJ


def check_z3_equivariance() -> bool:
    for shift in range(ORBIT_SIZE):
        permutation = z3_permutation(shift)
        matrix = np.eye(N_NODES)[permutation]
        if not np.allclose(matrix.T @ ADJ @ matrix, ADJ):
            return False
    return True


def generate_signals(n_samples: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    signals = rng.normal(size=(n_samples, N_NODES)) @ (np.eye(N_NODES) + 0.25 * ADJ)
    return (signals - signals.mean(axis=0)) / (signals.std(axis=0) + EPS)


def orbit_energy(signals: np.ndarray) -> np.ndarray:
    return np.column_stack([np.sum(signals[:, orbit] ** 2, axis=1) for orbit in ORBITS])


def orbit_mean(signals: np.ndarray) -> np.ndarray:
    return np.column_stack([np.mean(signals[:, orbit], axis=1) for orbit in ORBITS])


def orbit_abs_dev(signals: np.ndarray) -> np.ndarray:
    columns = []
    for orbit in ORBITS:
        mean = np.mean(signals[:, orbit], axis=1, keepdims=True)
        columns.append(np.mean(np.abs(signals[:, orbit] - mean), axis=1))
    return np.column_stack(columns)


def orbit_laplacian_energy(signals: np.ndarray) -> np.ndarray:
    transformed = signals @ LAPLACIAN.T
    return np.column_stack([np.sum(transformed[:, orbit] ** 2, axis=1) for orbit in ORBITS])


def orbit_laplacian_mean(signals: np.ndarray) -> np.ndarray:
    transformed = signals @ LAPLACIAN.T
    return np.column_stack([np.mean(transformed[:, orbit], axis=1) for orbit in ORBITS])


def fbohn_features(signals: np.ndarray) -> np.ndarray:
    return np.concatenate([orbit_energy(signals), orbit_mean(signals), orbit_abs_dev(signals),
                           orbit_laplacian_energy(signals), orbit_laplacian_mean(signals)], axis=1)


def fbohn_poly_control_features(signals: np.ndarray) -> np.ndarray:
    energy, mean, deviation = orbit_energy(signals), orbit_mean(signals), orbit_abs_dev(signals)
    lap_energy, lap_mean = orbit_laplacian_energy(signals), orbit_laplacian_mean(signals)
    blocks = [fbohn_features(signals), energy * lap_energy, energy * deviation,
              deviation * lap_energy, mean * lap_mean,
              np.sqrt(np.abs(energy * lap_energy) + EPS),
              np.sqrt(np.abs(deviation * lap_energy) + EPS),
              np.tanh(energy - lap_energy), np.tanh(deviation - lap_mean),
              np.tanh(mean + lap_mean)]
    return np.concatenate(blocks, axis=1)


OPS = ["add", "sub", "mul", "ratio", "sqrt_prod", "absdiff", "tanh_diff", "tanh_sum"]


def symbolic_op(left: np.ndarray, right: np.ndarray, operator: str) -> np.ndarray:
    if operator == "add": return left + right
    if operator == "sub": return left - right
    if operator == "mul": return left * right
    if operator == "ratio": return left / (np.abs(right) + EPS)
    if operator == "sqrt_prod": return np.sqrt(np.abs(left * right) + EPS)
    if operator == "absdiff": return np.abs(left - right)
    if operator == "tanh_diff": return np.tanh(left - right)
    if operator == "tanh_sum": return np.tanh(left + right)
    raise ValueError(operator)


def softplus(values: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(values))


def weighted_fbohn_orbitwise(signals: np.ndarray, theta: np.ndarray) -> np.ndarray:
    return fbohn_features(signals) * softplus(np.asarray(theta)).reshape(1, -1)
