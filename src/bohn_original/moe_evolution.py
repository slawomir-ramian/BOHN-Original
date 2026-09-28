"""Jawne prymitywy architektur MoE używane w testach Etapu 14."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class SharedBaseBN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
        )

    def forward(self, x):
        return self.net(x)


class SharedBaseLN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.ln1 = nn.GroupNorm(1, 32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.ln2 = nn.GroupNorm(1, 64)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.ln1(self.conv1(x))), 2)
        return F.max_pool2d(F.relu(self.ln2(self.conv2(x))), 2)


class ExpertTopLN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.conv = nn.Conv2d(64, 128, 3, padding=1)
        self.norm = nn.GroupNorm(1, 128)
        self.classifier = nn.Linear(128, n_classes)

    def forward(self, x):
        x = F.relu(self.norm(self.conv(x)))
        x = F.adaptive_avg_pool2d(x, 1).flatten(1)
        return self.classifier(x)


class ExpertTopBN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.conv = nn.Conv2d(64, 128, 3, padding=1)
        self.norm = nn.BatchNorm2d(128)
        self.classifier = nn.Linear(128, n_classes)

    def forward(self, x):
        x = F.relu(self.norm(self.conv(x)))
        x = F.adaptive_avg_pool2d(x, 1).flatten(1)
        return self.classifier(x)


class GateNetwork(nn.Module):
    def __init__(self, n_experts=4):
        super().__init__()
        self.net = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, n_experts))

    def forward(self, x):
        return self.net(x)


class HardAssignMoE(nn.Module):
    def __init__(self, n_experts=4, n_classes=10):
        super().__init__()
        self.base = SharedBaseBN()
        self.experts = nn.ModuleList([ExpertTopBN(n_classes) for _ in range(n_experts)])
        self.gate = GateNetwork(n_experts)

    def forward_hard(self, x, expert_idx):
        return self.experts[expert_idx](self.base(x))

    def forward_gated(self, x):
        features = self.base(x)
        gate_logits = self.gate(features)
        weights = F.softmax(gate_logits, dim=-1)
        outputs = torch.stack([expert(features) for expert in self.experts], dim=1)
        return (outputs * weights.unsqueeze(-1)).sum(1), gate_logits, weights


class ConfidenceRoutedMoE(nn.Module):
    def __init__(self, n_experts=3, n_classes=10):
        super().__init__()
        self.base = SharedBaseLN()
        self.experts = nn.ModuleList([ExpertTopLN(n_classes) for _ in range(n_experts)])

    def logits(self, x):
        features = self.base(x)
        return torch.stack([expert(features) for expert in self.experts], dim=1)

    def forward_confidence(self, x):
        all_logits = self.logits(x)
        probs = F.softmax(all_logits, dim=-1)
        entropy = -(probs * (probs + 1e-8).log()).sum(-1)
        selected = entropy.argmin(-1)
        return all_logits[torch.arange(x.size(0)), selected], selected


class HybridBNLNMoE(nn.Module):
    def __init__(self, n_experts=4, n_classes=10):
        super().__init__()
        self.base = SharedBaseBN()
        self.experts = nn.ModuleList([ExpertTopLN(n_classes) for _ in range(n_experts)])
        self.gate = GateNetwork(n_experts)

    def forward_hard(self, x, expert_idx):
        return self.experts[expert_idx](self.base(x))

    def forward_gated(self, x):
        features = self.base(x)
        gate_logits = self.gate(features)
        weights = F.softmax(gate_logits, dim=-1)
        outputs = torch.stack([expert(features) for expert in self.experts], dim=1)
        return (outputs * weights.unsqueeze(-1)).sum(1), gate_logits, weights


def routing_entropy(weights: torch.Tensor) -> torch.Tensor:
    return -(weights * (weights + 1e-8).log()).sum(-1)
