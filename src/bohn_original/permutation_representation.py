"""Małe, testowalne prymitywy Etapu 07; nie zastępują kodu historycznego."""
from __future__ import annotations

import numpy as np


def rotate_180(x: np.ndarray) -> np.ndarray:
    return np.rot90(x.reshape(-1, 8, 8), k=2, axes=(1, 2)).reshape(-1, 64)


def flip_horizontal(x: np.ndarray) -> np.ndarray:
    return x.reshape(-1, 8, 8)[:, :, ::-1].reshape(-1, 64)


def asymmetry(x: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    return np.abs(x - x[:, permutation])


def sum_asymmetry(x: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    px = x[:, permutation]
    return np.concatenate([x + px, np.abs(x - px)], axis=1)


def z3_permutation(dimension: int) -> np.ndarray:
    if dimension % 3:
        raise ValueError("dimension must be divisible by 3")
    block = dimension // 3
    return np.concatenate((np.arange(block, 2 * block), np.arange(2 * block, 3 * block), np.arange(block)))


def z3_features(x: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    gx = x[:, permutation]
    g2x = gx[:, permutation]
    return np.concatenate((x + gx + g2x, np.abs(x - gx), np.abs(x - g2x)), axis=1)


def linear_cka(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    a0 = a - a.mean(axis=0, keepdims=True)
    b0 = b - b.mean(axis=0, keepdims=True)
    numerator = np.linalg.norm(a0.T @ b0, ord="fro") ** 2
    denominator = np.linalg.norm(a0.T @ a0, ord="fro") * np.linalg.norm(b0.T @ b0, ord="fro")
    return float(numerator / (denominator + eps))
