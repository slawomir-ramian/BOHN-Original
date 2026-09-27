"""Małe, testowalne prymitywy geometrycznego Meta-SBOHN."""
from __future__ import annotations

import numpy as np


def geometry_features(image_size: int = 8) -> np.ndarray:
    axis = np.linspace(-1.0, 1.0, image_size)
    r, c = np.meshgrid(axis, axis, indexing="ij")
    r, c = r.ravel(), c.ravel()
    return np.column_stack([
        np.ones_like(r), r, c, r**2, c**2, r*c, r**3, c**3,
        np.sin(np.pi*r), np.sin(np.pi*c), np.cos(np.pi*r), np.cos(np.pi*c),
        np.sin(np.pi*(r+c)), np.cos(np.pi*(r-c)),
    ])


def theta_to_perm(theta: np.ndarray, features: np.ndarray | None = None) -> np.ndarray:
    values = geometry_features() if features is None else np.asarray(features)
    theta = np.asarray(theta, dtype=float)
    if values.shape[1] != theta.shape[0]:
        raise ValueError("Niezgodny wymiar theta")
    score = values @ theta
    return np.argsort(score + 1e-9 * np.arange(len(score)))


def lambda_schedule(mode: str, generation: int, generations: int) -> float:
    if mode == "accuracy_only":
        return 0.0
    if mode == "fixed_geometry":
        return 0.05
    if mode == "annealed_geometry":
        return 0.12 * (1.0 - generation / max(1, generations - 1))
    raise ValueError("Nieznany tryb")


def initialize_population(
    rng: np.random.Generator,
    population_size: int,
    n_theta: int = 14,
    init_theta: np.ndarray | None = None,
    transfer_elites: list[np.ndarray] | None = None,
    mode: str = "cold",
    init_sigma: float = 0.25,
    transfer_fraction: float = 0.5,
) -> list[np.ndarray]:
    if mode == "cold":
        return [rng.normal(size=n_theta) for _ in range(population_size)]
    if mode in {"warm", "mixed"} and init_theta is None:
        raise ValueError("init_theta jest wymagane")
    if mode in {"elite_warm", "elite_mixed"} and not transfer_elites:
        raise ValueError("transfer_elites są wymagane")
    if mode == "warm":
        return [init_theta.copy()] + [init_theta + init_sigma * rng.normal(size=n_theta) for _ in range(population_size - 1)]
    n_transfer = max(1, min(population_size - 1, int(round(population_size * transfer_fraction))))
    if mode == "mixed":
        population = [init_theta.copy()]
        while len(population) < n_transfer:
            population.append(init_theta + init_sigma * rng.normal(size=n_theta))
    elif mode in {"elite_warm", "elite_mixed"}:
        target = population_size if mode == "elite_warm" else n_transfer
        population = [value.copy() for value in transfer_elites[:target]]
        while len(population) < target:
            base = transfer_elites[rng.integers(0, len(transfer_elites))]
            population.append(base + init_sigma * rng.normal(size=n_theta))
    else:
        raise ValueError("Nieznany tryb")
    while len(population) < population_size:
        population.append(rng.normal(size=n_theta))
    rng.shuffle(population)
    return population
