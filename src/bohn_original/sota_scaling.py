"""Architektury z listingów 60–61 monografii BOHN."""
from __future__ import annotations

import torch
import torch.nn as nn


class SinkhornOp(nn.Module):
    def __init__(self, np_: int, fd: int, nh: int = 4):
        super().__init__()
        self.nh, self.np, self.hd = nh, np_, fd // nh
        self.la = nn.Parameter(torch.randn(nh, np_, np_) * 0.01)
        self.qn = nn.Linear(fd, nh * np_)
        self.op = nn.Linear(fd, fd)

    def forward(self, x):
        batch = x.shape[0]
        q = self.qn(x.mean(1)).view(batch, self.nh, self.np, 1)
        logits = self.la.unsqueeze(0) + q
        for _ in range(4):
            logits = logits - torch.logsumexp(logits, -1, True)
            logits = logits - torch.logsumexp(logits, -2, True)
        permutation = torch.exp(logits)
        heads = x.view(batch, self.np, self.nh, self.hd).permute(0, 2, 1, 3)
        mixed = torch.abs(heads - torch.matmul(permutation, heads))
        return self.op(mixed.permute(0, 2, 1, 3).reshape(batch, self.np, -1))


class FractalSBOHN(nn.Module):
    def __init__(self, ims=28, ch=1, nc=10, fd=16, nh=4):
        super().__init__()
        self.ps = max(4, ims // 4)
        self.np = (ims // self.ps) ** 2
        self.fd = fd
        self.pe = nn.Sequential(nn.Linear(ch * self.ps * self.ps, 64), nn.ReLU(), nn.Linear(64, fd))
        self.lvs, self.pls = nn.ModuleList(), nn.ModuleList()
        n = self.np
        for _ in range(3):
            if n < 4:
                break
            self.lvs.append(SinkhornOp(n, fd, nh))
            next_n = max(n // 2, 2)
            self.pls.append(nn.Linear(n * fd, next_n * fd))
            n = next_n
        self.fn = n
        self.cls = nn.Sequential(nn.Linear(n * fd, 64), nn.ReLU(), nn.Linear(64, nc))

    def forward(self, x):
        batch = x.shape[0]
        patches = x.unfold(2, self.ps, self.ps).unfold(3, self.ps, self.ps)
        patches = patches.permute(0, 2, 3, 1, 4, 5).contiguous().view(batch, self.np, -1)
        hidden = self.pe(patches)
        for layer, pool in zip(self.lvs, self.pls):
            hidden = pool(layer(hidden).reshape(batch, -1)).view(batch, -1, self.fd)
        return self.cls(hidden.reshape(batch, -1))


class CNN(nn.Module):
    def __init__(self, ch=1, nc=10):
        super().__init__()
        self.f = nn.Sequential(
            nn.Conv2d(ch, 16, 3, 1, 1), nn.ReLU(),
            nn.Conv2d(16, 32, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(64, nc)

    def forward(self, x):
        return self.fc(self.f(x).flatten(1))


class ViT(nn.Module):
    def __init__(self, ims=28, ch=1, nc=10, d=64, nh=4, nl=2):
        super().__init__()
        self.ps = max(4, ims // 4)
        self.np = (ims // self.ps) ** 2
        self.pe = nn.Linear(ch * self.ps * self.ps, d)
        self.pos = nn.Parameter(torch.randn(1, self.np + 1, d) * 0.02)
        self.ct = nn.Parameter(torch.randn(1, 1, d) * 0.02)
        self.tf = nn.TransformerEncoder(nn.TransformerEncoderLayer(d, nh, 128, 0.1, batch_first=True), nl)
        self.h = nn.Linear(d, nc)

    def forward(self, x):
        batch = x.shape[0]
        patches = x.unfold(2, self.ps, self.ps).unfold(3, self.ps, self.ps)
        patches = patches.permute(0, 2, 3, 1, 4, 5).contiguous().view(batch, self.np, -1)
        hidden = torch.cat([self.ct.expand(batch, -1, -1), self.pe(patches)], 1)
        hidden = hidden + self.pos[:, : hidden.size(1), :]
        return self.h(self.tf(hidden)[:, 0])


class MLP(nn.Module):
    def __init__(self, input_size, nc=10):
        super().__init__()
        self.n = nn.Sequential(
            nn.Flatten(), nn.Linear(input_size, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, nc),
        )

    def forward(self, x):
        return self.n(x)


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def parameter_memory_mb(model: nn.Module) -> float:
    return sum(p.nelement() * p.element_size() for p in model.parameters()) / 1e6
