"""Supplementary high-resolution models for BOHN Stage 16.

This module does not replace the historical SOTA-002 implementation.  The
hierarchical front-end is an explicitly new architecture that feeds the same
16-token Sinkhorn cascade used by the historical FractalSBOHN model.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from bohn_original.sota_scaling import SinkhornOp


class HierarchicalFractalSBOHN(nn.Module):
    """Resolution-independent front-end followed by the BOHN relational core."""

    def __init__(self, ch: int = 1, nc: int = 10, fd: int = 16, nh: int = 4):
        super().__init__()
        self.fd = fd
        self.np = 16
        self.encoder = nn.Sequential(
            nn.Conv2d(ch, 8, kernel_size=5, stride=2, padding=2),
            nn.GELU(),
            nn.Conv2d(8, fd, kernel_size=3, stride=2, padding=1),
            nn.GELU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.lvs = nn.ModuleList()
        self.pls = nn.ModuleList()
        n = self.np
        for _ in range(3):
            self.lvs.append(SinkhornOp(n, fd, nh))
            next_n = max(n // 2, 2)
            self.pls.append(nn.Linear(n * fd, next_n * fd))
            n = next_n
        self.fn = n
        self.cls = nn.Sequential(
            nn.Linear(n * fd, 64),
            nn.ReLU(),
            nn.Linear(64, nc),
        )

    def encode_tokens(self, x: torch.Tensor) -> torch.Tensor:
        """Return exactly 16 tokens for every positive spatial resolution."""
        return self.encoder(x).flatten(2).transpose(1, 2).contiguous()

    def relational_core(self, tokens: torch.Tensor) -> torch.Tensor:
        """Run the unchanged 16 -> 8 -> 4 -> 2 Sinkhorn/pooling cascade."""
        batch = tokens.shape[0]
        hidden = tokens
        for layer, pool in zip(self.lvs, self.pls):
            hidden = pool(layer(hidden).reshape(batch, -1)).view(batch, -1, self.fd)
        return self.cls(hidden.reshape(batch, -1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relational_core(self.encode_tokens(x))


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())

