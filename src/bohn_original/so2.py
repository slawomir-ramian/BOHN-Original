"""Jawne narzędzia rekonstrukcyjne SO(2) dla Etapu 05.

Ten moduł nie jest przedstawiany jako historyczny listing. Implementuje wzory
opublikowane w rozdziale 4 monografii i uzupełnia brakujący protokół wykonawczy.
"""

from __future__ import annotations

import math

import numpy as np


def rotation_matrix(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def rotate_blocks(X: np.ndarray, theta: float) -> np.ndarray:
    if X.ndim != 2 or X.shape[1] % 2:
        raise ValueError("SO(2) block representation requires an even feature dimension")
    blocks = X.reshape(X.shape[0], -1, 2)
    rotated = blocks @ rotation_matrix(theta).T
    return rotated.reshape(X.shape)


def numerical_symmetrizer(x: np.ndarray, n_theta: int) -> np.ndarray:
    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    rotations = np.stack(
        [np.cos(thetas), -np.sin(thetas), np.sin(thetas), np.cos(thetas)], axis=1
    ).reshape(-1, 2, 2)
    return np.mean(rotations @ x, axis=0)


def asymmetry_profile(x: np.ndarray, thetas: np.ndarray) -> np.ndarray:
    rotated = np.stack([rotation_matrix(theta) @ x for theta in thetas])
    return np.linalg.norm(x - rotated, axis=1)


def analytical_profile(radius: float, thetas: np.ndarray) -> np.ndarray:
    return 2.0 * radius * np.abs(np.sin(thetas / 2.0))


def analytical_moment(radius: float, order: int) -> float:
    beta = math.gamma((order + 1) / 2.0) * math.gamma(0.5) / math.gamma((order + 2) / 2.0)
    return (2.0 * radius) ** order * beta / math.pi


def moment_features(X: np.ndarray, k: int = 4, n_theta: int = 500) -> np.ndarray:
    """Dyskretne momenty profilu, obliczone z opublikowanego wzoru SO(2)."""
    if X.ndim != 2 or X.shape[1] % 2:
        raise ValueError("SO(2) block representation requires an even feature dimension")
    radii = np.linalg.norm(X.reshape(X.shape[0], -1, 2), axis=2)
    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    base = 2.0 * np.abs(np.sin(thetas / 2.0))
    coefficients = np.array([np.mean(base ** order) for order in range(1, k + 1)])
    powers = np.stack([radii ** order for order in range(1, k + 1)], axis=2)
    return (powers * coefficients).reshape(X.shape[0], -1)


def make_radial_classification_dataset(
    n_samples: int,
    n_blocks: int,
    seed: int,
    radial_noise: float = 0.03,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rekonstrukcja scenariusza klas różniących się układem promieni."""
    rng = np.random.default_rng(seed)
    y = np.arange(n_samples, dtype=int) % 2
    rng.shuffle(y)
    low = 1.0
    high = 2.4
    radii = np.empty((n_samples, n_blocks), dtype=float)
    for block in range(n_blocks):
        radii[:, block] = np.where((y + block) % 2 == 0, low, high)
    radii += rng.normal(scale=radial_noise, size=radii.shape)
    angles = rng.uniform(0.0, 2.0 * np.pi, size=(n_samples, n_blocks))
    pairs = np.stack([radii * np.cos(angles), radii * np.sin(angles)], axis=2)
    return pairs.reshape(n_samples, 2 * n_blocks), y, radii


def classification_scores(n_blocks: int, seed: int = 42) -> dict[str, float]:
    """Odtwórz jakościowy protokół klasyfikacji opisany w monografii."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X, y, radii = make_radial_classification_dataset(
        n_samples=2400, n_blocks=n_blocks, seed=seed
    )
    indices = np.arange(len(X))
    train, test = train_test_split(
        indices, test_size=0.30, random_state=seed, stratify=y
    )
    features = moment_features(X, k=4, n_theta=500)

    def logistic(data: np.ndarray) -> float:
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        model.fit(data[train], y[train])
        return accuracy_score(y[test], model.predict(data[test]))

    forest = RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=1)
    forest.fit(X[train], y[train])
    raw_forest = accuracy_score(y[test], forest.predict(X[test]))
    forest_features = RandomForestClassifier(
        n_estimators=300, random_state=seed, n_jobs=1
    )
    forest_features.fit(features[train], y[train])
    feature_forest = accuracy_score(y[test], forest_features.predict(features[test]))
    return {
        "raw_logistic": logistic(X),
        "raw_forest": raw_forest,
        "feature_logistic": logistic(features),
        "feature_forest": feature_forest,
        "oracle_logistic": logistic(radii),
    }
