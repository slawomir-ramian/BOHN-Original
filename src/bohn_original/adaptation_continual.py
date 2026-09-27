"""Jawne prymitywy rekonstrukcji Etapu 11.

Architektury odtwarzają opublikowane fragmenty listingów 58 i 59. Kod
historyczny pozostaje osobno w katalogach ``historical``; ten moduł uzupełnia
wyłącznie fazy eksperymentalne pominięte w monografii.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

import torch
import torch.nn as nn


def sinkhorn(log_alpha: torch.Tensor, n_iter: int = 10, tau: float = 0.1) -> torch.Tensor:
    values = log_alpha / tau
    for _ in range(n_iter):
        values = values - torch.logsumexp(values, dim=-1, keepdim=True)
        values = values - torch.logsumexp(values, dim=-2, keepdim=True)
    return values.exp()


class PermHeadSBOHN(nn.Module):
    """Architektura listingu 58: 46 106 parametrów, w tym 714 per task."""

    def __init__(self, patch_size: int = 7, n_patches: int = 4,
                 features_per_patch: int = 16, n_heads: int = 4,
                 n_classes: int = 10):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.n_heads = n_heads
        self.features_per_patch = features_per_patch
        patch_dim = patch_size * patch_size
        self.patch_encoder = nn.Sequential(
            nn.Linear(patch_dim, 64), nn.ReLU(),
            nn.Linear(64, features_per_patch),
        )
        self.perm_logits = nn.ParameterList([
            nn.Parameter(torch.randn(n_patches, n_patches) * 0.1)
            for _ in range(n_heads)
        ])
        total_features = n_patches * features_per_patch * n_heads
        self.hidden = nn.Sequential(
            nn.Linear(total_features, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
        )
        self.classifier = nn.Linear(64, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch = x.shape[0]
        p = self.patch_size
        patches = []
        for row in range(2):
            for col in range(2):
                patches.append(x[:, :, row*p:(row+1)*p, col*p:(col+1)*p].reshape(batch, -1))
        encoded = self.patch_encoder(torch.stack(patches, dim=1))
        outputs = []
        for logits in self.perm_logits:
            matrix = sinkhorn(logits.unsqueeze(0).expand(batch, -1, -1))
            outputs.append((encoded * torch.bmm(matrix, encoded)).reshape(batch, -1))
        return self.classifier(self.hidden(torch.cat(outputs, dim=1)))

    def encoder_params(self) -> list[nn.Parameter]:
        return list(self.patch_encoder.parameters()) + list(self.hidden.parameters())

    def adaptation_params(self) -> list[nn.Parameter]:
        return list(self.classifier.parameters()) + list(self.perm_logits)

    def perm_only_params(self) -> list[nn.Parameter]:
        return list(self.perm_logits)

    def head_only_params(self) -> list[nn.Parameter]:
        return list(self.classifier.parameters())

    def save_task_params(self) -> dict[str, object]:
        return {
            "perm": [parameter.detach().clone() for parameter in self.perm_logits],
            "head_w": self.classifier.weight.detach().clone(),
            "head_b": self.classifier.bias.detach().clone(),
        }

    def load_task_params(self, saved: dict[str, object]) -> None:
        with torch.no_grad():
            for parameter, value in zip(self.perm_logits, saved["perm"]):
                parameter.copy_(value)
            self.classifier.weight.copy_(saved["head_w"])
            self.classifier.bias.copy_(saved["head_b"])


class PermHeadMLP(nn.Module):
    def __init__(self, n_classes: int = 10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Flatten(), nn.Linear(784, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(),
        )
        self.classifier = nn.Linear(64, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.encoder(x))


class FewShotSBOHN(nn.Module):
    """Architektura listingu 59: 170 522 parametry, 1024 permutacyjne."""

    def __init__(self, img_size: int = 28, patch_size: int = 7,
                 features_per_patch: int = 16, n_heads: int = 4,
                 n_classes: int = 10):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2
        self.features_per_patch = features_per_patch
        self.n_heads = n_heads
        pixels = patch_size * patch_size
        self.patch_encoder = nn.Sequential(
            nn.Linear(pixels, 64), nn.ReLU(), nn.Linear(64, features_per_patch)
        )
        self.sinkhorn_logits = nn.ParameterList([
            nn.Parameter(torch.randn(self.n_patches, self.n_patches) * 0.1)
            for _ in range(n_heads)
        ])
        total = features_per_patch * self.n_patches
        self.head = nn.Sequential(
            nn.Linear(total * (n_heads + 1), 128), nn.ReLU(), nn.Linear(128, n_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch = x.shape[0]
        p = self.patch_size
        side = int(self.n_patches ** 0.5)
        image = x.view(batch, 1, side * p, side * p)
        patches = image.unfold(2, p, p).unfold(3, p, p)
        patches = patches.contiguous().view(batch, self.n_patches, p * p)
        features = self.patch_encoder(patches)
        branches = [features.view(batch, -1)]
        for logits in self.sinkhorn_logits:
            matrix = sinkhorn(logits.unsqueeze(0).expand(batch, -1, -1))
            branches.append(torch.bmm(matrix, features).reshape(batch, -1))
        return self.head(torch.cat(branches, dim=-1))

    def perm_only_params(self) -> list[nn.Parameter]:
        return list(self.sinkhorn_logits)

    def head_only_params(self) -> list[nn.Parameter]:
        return list(self.head.parameters())

    def save_permutations(self) -> list[torch.Tensor]:
        return [parameter.detach().clone() for parameter in self.sinkhorn_logits]

    def load_permutations(self, saved: list[torch.Tensor]) -> None:
        with torch.no_grad():
            for parameter, value in zip(self.sinkhorn_logits, saved):
                parameter.copy_(value)


class SimpleMLP(nn.Module):
    def __init__(self, n_classes: int = 10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.view(x.size(0), -1))


class SimpleCNN(nn.Module):
    def __init__(self, n_classes: int = 10):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.fc = nn.Sequential(nn.Linear(32 * 7 * 7, 128), nn.ReLU(), nn.Linear(128, n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = self.conv(x.view(-1, 1, 28, 28))
        return self.fc(hidden.view(hidden.size(0), -1))


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def parameter_count_of(parameters: Iterable[nn.Parameter]) -> int:
    return sum(parameter.numel() for parameter in parameters)


def state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().clone() for key, value in model.state_dict().items()}


def model_copy(model: nn.Module) -> nn.Module:
    return deepcopy(model)


def select_trainable(model: nn.Module, parameters: Iterable[nn.Parameter]) -> list[nn.Parameter]:
    chosen = list(parameters)
    chosen_ids = {id(parameter) for parameter in chosen}
    for parameter in model.parameters():
        parameter.requires_grad_(id(parameter) in chosen_ids)
    return chosen
