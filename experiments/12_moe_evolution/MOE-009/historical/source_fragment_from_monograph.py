"""
BOHN: Partial Unfreeze (Last 2 Layers) + MoE
=============================================
Key idea: Each expert gets its OWN copy of unfrozen layers.
Shared frozen base -> Expert-specific top layers + perm + head.
This gives adaptation WITHOUT catastrophic forgetting!
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import json
import time
import numpy as np

torch.manual_seed(42)
device = 'cpu'

# ============================================================
# 1. DATA: 4 domains
# ============================================================
print("=" * 60)
print("BOHN: PARTIAL UNFREEZE + MoE")
print("=" * 60)

transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
transform_rgb = transforms.Compose([
    transforms.Grayscale(1), transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))
])

def load_subset(dataset, n=2000):
    loader = torch.utils.data.DataLoader(dataset, batch_size=n, shuffle=True)
    x, y = next(iter(loader))
    return x, y

datasets = {}
for name, ds_class, tf in [
    ('MNIST', torchvision.datasets.MNIST, transform),
    ('Fashion', torchvision.datasets.FashionMNIST, transform),
    ('KMNIST', torchvision.datasets.KMNIST, transform),
]:
    ds = ds_class('/tmp/data', train=True, download=True, transform=tf)
    ds_test = ds_class('/tmp/data', train=False, download=True, transform=tf)
    x_tr, y_tr = load_subset(ds, 3000)
    x_te, y_te = load_subset(ds_test, 1000)
    datasets[name] = {'train': (x_tr, y_tr), 'test': (x_te, y_te)}
    print(f"  {name}: train={x_tr.shape[0]}, test={x_te.shape[0]}")

# ============================================================
# 2. ARCHITECTURE: Shared Frozen Base + Expert-Specific Top
# ============================================================
class SharedEncoder(nn.Module):
    """4-layer encoder. Layers 1-2 = frozen base, layers 3-4 = template for experts."""
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.layer4 = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )

    def forward_base(self, x):
        return self.layer2(self.layer1(x))

    def forward_top(self, x):
        x = self.layer4(self.layer3(x))
        return x.view(x.size(0), -1)

    def forward(self, x):
        return self.forward_top(self.forward_base(x))


class ExpertModule(nn.Module):
    """One expert = own top layers + Sinkhorn permutation + classifier"""
    def __init__(self, feature_dim=256, n_classes=10, n_heads=4):
        super().__init__()
        self.layer3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.layer4 = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.n_heads = n_heads
        self.head_dim = feature_dim // n_heads
        self.perm_logits = nn.ParameterList([
            nn.Parameter(torch.randn(self.head_dim, self.head_dim) * 0.1)
            for _ in range(n_heads)
        ])
        self.classifier = nn.Linear(feature_dim, n_classes)

    def sinkhorn(self, log_alpha, n_iter=10):
        for _ in range(n_iter):
            log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
            log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
        return torch.exp(log_alpha)

    def forward_features(self, base_features):
        x = self.layer4(self.layer3(base_features))
        return x.view(x.size(0), -1)

    def forward(self, features):
        heads = features.split(self.head_dim, dim=-1)
        permuted = []
        for i, h in enumerate(heads):
            P = self.sinkhorn(self.perm_logits[i])
            permuted.append(h @ P)
        x = torch.cat(permuted, dim=-1)
        return self.classifier(x)


class MoEWithPartialUnfreeze(nn.Module):
    """Full system: frozen base + N experts + gate"""
    def __init__(self, shared_encoder, n_experts=4, feature_dim=256, n_classes=10):
        super().__init__()
        self.shared_encoder = shared_encoder
        self.n_experts = n_experts

        for param in self.shared_encoder.layer1.parameters():
            param.requires_grad = False
        for param in self.shared_encoder.layer2.parameters():
            param.requires_grad = False

        self.experts = nn.ModuleList([
            ExpertModule(feature_dim, n_classes) for _ in range(n_experts)
        ])
        for expert in self.experts:
            expert.layer3.load_state_dict(shared_encoder.layer3.state_dict())
            expert.layer4.load_state_dict(shared_encoder.layer4.state_dict())

        self.gate = nn.Sequential(
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, n_experts),
        )

    def forward(self, x, return_gate=False):
        with torch.no_grad():
            base = self.shared_encoder.forward_base(x)
        gate_logits = self.gate(base.detach())
        gate_weights = F.softmax(gate_logits, dim=-1)
        expert_outputs = []
        for expert in self.experts:
            feat = expert.forward_features(base)
            out = expert(feat)
            expert_outputs.append(out)
        expert_stack = torch.stack(expert_outputs, dim=1)
        gate_expanded = gate_weights.unsqueeze(-1)
        output = (expert_stack * gate_expanded).sum(dim=1)
        if return_gate:
            return output, gate_weights
        return output
