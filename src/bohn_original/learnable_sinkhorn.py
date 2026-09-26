"""Minimalne prymitywy numeryczne Etapu 08."""
from __future__ import annotations

import torch


def naive_sinkhorn(scores: torch.Tensor, n_iters: int = 20, tau: float = 1.0) -> torch.Tensor:
    """Wersja publikacyjna: eksponenta i naprzemienna normalizacja."""
    scaled = scores / tau
    values = torch.exp(scaled - scaled.amax(dim=-1, keepdim=True))
    for _ in range(n_iters):
        values = values / (values.sum(dim=-1, keepdim=True) + 1e-9)
        values = values / (values.sum(dim=-2, keepdim=True) + 1e-9)
    return values


def log_sinkhorn(scores: torch.Tensor, n_iters: int = 20, tau: float = 1.0) -> torch.Tensor:
    """Stabilna normalizacja Sinkhorna wykonywana w dziedzinie logarytmów."""
    log_values = scores / tau
    for _ in range(n_iters):
        log_values = log_values - torch.logsumexp(log_values, dim=-1, keepdim=True)
        log_values = log_values - torch.logsumexp(log_values, dim=-2, keepdim=True)
    return torch.exp(log_values)


def doubly_stochastic_error(matrix: torch.Tensor) -> float:
    row_error = (matrix.sum(dim=-1) - 1).abs().mean()
    column_error = (matrix.sum(dim=-2) - 1).abs().mean()
    return float(row_error + column_error)


def row_entropy(matrix: torch.Tensor) -> torch.Tensor:
    return -(matrix * torch.log(matrix + 1e-10)).sum(dim=-1).mean()
