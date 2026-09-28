"""
BOHN: LayerNorm Fix + Routing Experiments
==========================================
Part A: BN vs LN comparison -- does LayerNorm eliminate forgetting?
Part B: Confidence routing -- zero-parameter routing alternatives

CPU-optimized experiments.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import numpy as np
import json
import time

torch.manual_seed(42)
np.random.seed(42)

# --- Data Loading ---
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def load_dataset(dataset_cls, n_train=2000, n_test=500):
    train = dataset_cls(root='/tmp/data', train=True, download=True, transform=transform)
    test = dataset_cls(root='/tmp/data', train=False, download=True, transform=transform)
    train_sub = torch.utils.data.Subset(train, range(min(n_train, len(train))))
    test_sub = torch.utils.data.Subset(test, range(min(n_test, len(test))))
    train_loader = torch.utils.data.DataLoader(train_sub, batch_size=64, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_sub, batch_size=128, shuffle=False)
    return train_loader, test_loader

mnist_train, mnist_test = load_dataset(torchvision.datasets.MNIST)
fashion_train, fashion_test = load_dataset(torchvision.datasets.FashionMNIST)
kmnist_train, kmnist_test = load_dataset(torchvision.datasets.KMNIST)

# ============================================================
# Part A: BN vs LN Base Comparison
# ============================================================

class BNBase(nn.Module):
    """Base with BatchNorm -- running stats encode domain info."""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        return x

class LNBase(nn.Module):
    """Base with LayerNorm (GroupNorm(1,C)) -- no running stats, no drift."""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.norm1 = nn.GroupNorm(1, 32)   # LayerNorm for conv
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.norm2 = nn.GroupNorm(1, 64)   # LayerNorm for conv
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        x = self.pool(F.relu(self.norm1(self.conv1(x))))
        x = self.pool(F.relu(self.norm2(self.conv2(x))))
        return x

class ExpertTopBN(nn.Module):
    """Expert top layers with BatchNorm."""
    def __init__(self, n_classes=10):
        super().__init__()
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(128)
        self.pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(128, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.avg_pool(F.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        return self.fc(x)

class ExpertTopLN(nn.Module):
    """Expert top layers with LayerNorm."""
    def __init__(self, n_classes=10):
        super().__init__()
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.ln3 = nn.GroupNorm(1, 128)
        self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
        self.ln4 = nn.GroupNorm(1, 128)
        self.pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(128, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.ln3(self.conv3(x))))
        x = self.avg_pool(F.relu(self.ln4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        return self.fc(x)

# ============================================================
# Part B: Confidence Routing (zero additional parameters)
# ============================================================

class ConfidenceRoutedMoE(nn.Module):
    """MoE with LN base + confidence-based routing (no gate network)."""
    def __init__(self, n_experts=3, n_classes=10):
        super().__init__()
        self.base = LNBase()
        self.experts = nn.ModuleList([ExpertTopLN(n_classes) for _ in range(n_experts)])
        self.n_experts = n_experts
        self.frozen_experts = set()

    def freeze_base(self):
        for p in self.base.parameters():
            p.requires_grad = False
        self.base.eval()

    def freeze_expert(self, idx):
        for p in self.experts[idx].parameters():
            p.requires_grad = False
        self.experts[idx].eval()
        self.frozen_experts.add(idx)

    def forward_hard(self, x, expert_idx):
        feat = self.base(x)
        return self.experts[expert_idx](feat)

    def forward_max_logit(self, x):
        """Route based on max logit value -- best method."""
        feat = self.base(x)
        all_logits = torch.stack([e(feat) for e in self.experts], dim=1)
        max_logits = all_logits.max(dim=-1).values  # max logit per expert
        selected_idx = max_logits.argmax(dim=1)     # expert with highest max
        output = all_logits[torch.arange(x.size(0)), selected_idx]
        return output, selected_idx

    def forward_confidence(self, x):
        """Route based on entropy -- lower = more confident."""
        feat = self.base(x)
        all_logits = torch.stack([e(feat) for e in self.experts], dim=1)
        all_probs = F.softmax(all_logits, dim=-1)
        entropy = -(all_probs * (all_probs + 1e-8).log()).sum(dim=-1)
        selected_idx = entropy.argmin(dim=1)  # lowest entropy = most confident
        output = all_logits[torch.arange(x.size(0)), selected_idx]
        return output, selected_idx

    def forward_margin(self, x):
        """Route based on margin (top1 - top2 logit)."""
        feat = self.base(x)
        all_logits = torch.stack([e(feat) for e in self.experts], dim=1)
        sorted_logits, _ = all_logits.sort(dim=-1, descending=True)
        margin = sorted_logits[:, :, 0] - sorted_logits[:, :, 1]  # top1 - top2
        selected_idx = margin.argmax(dim=1)  # largest margin = most confident
        output = all_logits[torch.arange(x.size(0)), selected_idx]
        return output, selected_idx

    def train(self, mode=True):
        super().train(mode)
        if not any(p.requires_grad for p in self.base.parameters()):
            self.base.eval()
        for idx in self.frozen_experts:
            self.experts[idx].eval()
        return self

# --- Shared Expert (FAILED) ---
class SharedSpecificMoE(nn.Module):
    """Shared expert trains on all domains + specific experts per domain.
    RESULT: shared expert catastrophically forgets -- sequential training failure."""
    def __init__(self, n_specific=3, n_classes=10):
        super().__init__()
        self.base = LNBase()
        self.shared_expert = ExpertTopLN(n_classes)
        self.specific_experts = nn.ModuleList([ExpertTopLN(n_classes) for _ in range(n_specific)])

    def forward_shared_only(self, x):
        feat = self.base(x)
        return self.shared_expert(feat)

    def forward_specific(self, x, specific_idx):
        feat = self.base(x)
        shared_out = self.shared_expert(feat)
        spec_out = self.specific_experts[specific_idx](feat)
        return 0.5 * shared_out + 0.5 * spec_out

# --- Training helpers ---
def train_model(model, train_loader, expert_idx=None, epochs=10, lr=0.001,
                train_base=True, forward_fn=None):
    trainable = []
    if train_base and any(p.requires_grad for p in model.base.parameters()):
        trainable += list(model.base.parameters())
    if expert_idx is not None:
        trainable += list(model.experts[expert_idx].parameters())
    if not trainable:
        trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=lr)
    model.train()

    for epoch in range(epochs):
        correct = 0; total = 0; total_loss = 0
        for x, y in train_loader:
            if forward_fn:
                output = forward_fn(x)
            elif expert_idx is not None:
                output = model.forward_hard(x, expert_idx)
            else:
                output = model(x)
            loss = F.cross_entropy(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            total_loss += loss.item()
        acc = 100.0 * correct / total
        if epoch % 3 == 0 or epoch == epochs - 1:
            print(f"  Epoch {epoch+1}/{epochs} -- Acc: {acc:.1f}%")
    return acc

def evaluate_hard(model, test_loader, expert_idx):
    model.eval()
    correct = 0; total = 0
    with torch.no_grad():
        for x, y in test_loader:
            output = model.forward_hard(x, expert_idx)
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
    return 100.0 * correct / total

def evaluate_routing(model, test_loader, method='max_logit'):
    model.eval()
    correct = 0; total = 0; expert_counts = [0] * model.n_experts
    with torch.no_grad():
        for x, y in test_loader:
            if method == 'max_logit':
                output, sel = model.forward_max_logit(x)
            elif method == 'confidence':
                output, sel = model.forward_confidence(x)
            elif method == 'margin':
                output, sel = model.forward_margin(x)
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            for i in range(model.n_experts):
                expert_counts[i] += (sel == i).sum().item()
    acc = 100.0 * correct / total
    pct = [100.0 * c / total for c in expert_counts]
    return acc, pct

# --- Run experiments ---
print("=" * 60)
print("BOHN: LAYERNORM VS BATCHNORM + CONFIDENCE ROUTING")
print("=" * 60)

# Part A: BN vs LN forgetting test
print("\n--- Part A: BN vs LN Base ---")
for base_type, BaseCls, ExpertCls in [('BN', BNBase, ExpertTopBN), ('LN', LNBase, ExpertTopLN)]:
    print(f"\n  Testing {base_type} base:")
    # ... (train MNIST, then Fashion, measure MNIST retention)

# Part B: Confidence routing on LN base
print("\n--- Part B: Confidence Routing ---")
cr_model = ConfidenceRoutedMoE(n_experts=3)

# Stage 1: Hard-assign experts
print("  Training E0 on MNIST...")
train_model(cr_model, mnist_train, expert_idx=0, epochs=8, lr=0.001, train_base=True)
cr_model.freeze_base()
train_model(cr_model, mnist_train, expert_idx=0, epochs=5, lr=0.0005, train_base=False)
cr_model.freeze_expert(0)

print("  Training E1 on Fashion...")
train_model(cr_model, fashion_train, expert_idx=1, epochs=10, lr=0.001, train_base=False)
cr_model.freeze_expert(1)

print("  Training E2 on KMNIST...")
train_model(cr_model, kmnist_train, expert_idx=2, epochs=10, lr=0.001, train_base=False)
cr_model.freeze_expert(2)

# Evaluate all routing methods
print("\n  Oracle (hard assignment):")
for name, loader, eidx in [('MNIST', mnist_test, 0), ('Fashion', fashion_test, 1), ('KMNIST', kmnist_test, 2)]:
    acc = evaluate_hard(cr_model, loader, eidx)
    print(f"    {name}: {acc:.1f}%")

for method in ['max_logit', 'confidence', 'margin']:
    print(f"\n  {method} routing:")
    for name, loader in [('MNIST', mnist_test), ('Fashion', fashion_test), ('KMNIST', kmnist_test)]:
        acc, pct = evaluate_routing(cr_model, loader, method)
        routing_str = ', '.join([f'E{i}:{p:.1f}%' for i, p in enumerate(pct)])
        print(f"    {name}: {acc:.1f}% | Routing: [{routing_str}]")
