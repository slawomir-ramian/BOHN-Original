"""Małe, testowalne prymitywy architektur fraktalnych i patchowych."""
from __future__ import annotations

import torch
import torch.nn.functional as F


def log_sinkhorn(log_alpha: torch.Tensor, n_iter: int = 10, tau: float = 1.0) -> torch.Tensor:
    values = log_alpha / tau
    for _ in range(n_iter):
        values = values - torch.logsumexp(values, dim=-1, keepdim=True)
        values = values - torch.logsumexp(values, dim=-2, keepdim=True)
    return values.exp()


def doubly_stochastic_error(matrix: torch.Tensor) -> float:
    row = (matrix.sum(dim=-1) - 1.0).abs().max()
    col = (matrix.sum(dim=-2) - 1.0).abs().max()
    return float(torch.maximum(row, col))


def multiscale_features(images: torch.Tensor, levels: int = 4) -> list[torch.Tensor]:
    if images.ndim != 4:
        raise ValueError("Oczekiwano tensora BxCxHxW")
    sizes = (4, 8, 16, 32)
    if not 1 <= levels <= len(sizes):
        raise ValueError("levels musi należeć do 1..4")
    batch = images.shape[0]
    return [F.adaptive_avg_pool2d(images, size).reshape(batch, -1) for size in sizes[:levels]]


def extract_patches(images: torch.Tensor, patch_size: int = 8) -> torch.Tensor:
    if images.ndim == 4 and images.shape[1] == 1:
        images = images[:, 0]
    if images.ndim != 3:
        raise ValueError("Oczekiwano tensora BxHxW lub Bx1xHxW")
    batch, height, width = images.shape
    if height % patch_size or width % patch_size:
        raise ValueError("Rozmiar obrazu musi być podzielny przez patch_size")
    return (
        images.reshape(batch, height // patch_size, patch_size, width // patch_size, patch_size)
        .permute(0, 1, 3, 2, 4)
        .reshape(batch, (height // patch_size) * (width // patch_size), patch_size * patch_size)
    )


def permute_patch_sequence(patches: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    if patches.ndim != 3 or matrix.ndim != 3:
        raise ValueError("Oczekiwano patches BxNxD oraz matrix BxNxN")
    return torch.bmm(matrix, patches)
