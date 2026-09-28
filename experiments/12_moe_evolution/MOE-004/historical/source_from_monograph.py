"""
BOHN: Hard Assignment + Gate Distillation
==========================================
3-stage pipeline:
1. Hard-assign experts to domains (one expert per domain)
2. Gate distillation (gate learns to replicate assignments)
3. Freeze & expand (add new domains to free expert slots)
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

# --- SharedFrozenBase ---
class SharedFrozenBase(nn.Module):
    """Shared base: conv1(1->32) + BN + pool + conv2(32->64) + BN + pool -> [B, 64, 7, 7]"""
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

# --- ExpertTop ---
class SinkhornPermutation(nn.Module):
    def __init__(self, dim, n_iters=5, tau=0.1):
        super().__init__()
        self.log_alpha = nn.Parameter(torch.randn(dim, dim) * 0.01)
        self.n_iters = n_iters
        self.tau = tau

    def forward(self, x):
        log_a = self.log_alpha / self.tau
        for _ in range(self.n_iters):
            log_a = log_a - torch.logsumexp(log_a, dim=1, keepdim=True)
            log_a = log_a - torch.logsumexp(log_a, dim=0, keepdim=True)
        P = torch.exp(log_a)
        flat = x.view(x.size(0), -1)
        if flat.size(1) == P.size(0):
            return (flat @ P).view_as(x)
        return x

class ExpertTop(nn.Module):
    """Per-expert: conv3(64->128) + conv4(128->128) + pool -> flatten
       Sinkhorn permutation on first 64 dims
       fc1(1152->256) + dropout + fc2(256->10)"""
    def __init__(self, n_classes=10, perm_size=64):
        super().__init__()
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(128)
        self.pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AdaptiveAvgPool2d(3)
        self.sinkhorn = SinkhornPermutation(perm_size)
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(256, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.avg_pool(F.relu(self.bn4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        # Apply Sinkhorn on first 64 dims
        perm_part = self.sinkhorn(x[:, :64])
        x = torch.cat([perm_part, x[:, 64:]], dim=1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)

# --- GateNetwork ---
class GateNetwork(nn.Module):
    """Linear(3136->128) + ReLU + BN + Dropout + Linear(128->64) + ReLU + Linear(64->4)"""
    def __init__(self, input_dim=64*7*7, n_experts=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, n_experts)
        )

    def forward(self, x):
        flat = x.view(x.size(0), -1)
        return self.net(flat)

# --- HardAssignMoE ---
class HardAssignMoE(nn.Module):
    """Orchestrator: shared base + N experts + gate"""
    def __init__(self, n_experts=4, n_classes=10):
        super().__init__()
        self.base = SharedFrozenBase()
        self.experts = nn.ModuleList([ExpertTop(n_classes) for _ in range(n_experts)])
        self.gate = GateNetwork(input_dim=64*7*7, n_experts=n_experts)
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
        """Hard assignment -- one expert per input"""
        feat = self.base(x)
        return self.experts[expert_idx](feat)

    def forward_gated(self, x, top_k=2):
        """Gated inference -- gate selects top-k experts"""
        feat = self.base(x)
        gate_logits = self.gate(feat)
        gate_weights = F.softmax(gate_logits, dim=-1)

        if top_k < self.n_experts:
            topk_vals, topk_idx = torch.topk(gate_weights, top_k, dim=-1)
            mask = torch.zeros_like(gate_weights).scatter_(1, topk_idx, 1.0)
            gate_weights = gate_weights * mask
            gate_weights = gate_weights / (gate_weights.sum(dim=-1, keepdim=True) + 1e-8)

        expert_outputs = []
        for i, expert in enumerate(self.experts):
            out = expert(feat)
            expert_outputs.append(out)

        expert_stack = torch.stack(expert_outputs, dim=1)
        gate_expanded = gate_weights.unsqueeze(-1)
        output = (expert_stack * gate_expanded).sum(dim=1)
        return output, gate_logits, gate_weights

    def train(self, mode=True):
        super().train(mode)
        # Keep frozen components in eval mode
        if not any(p.requires_grad for p in self.base.parameters()):
            self.base.eval()
        for idx in self.frozen_experts:
            self.experts[idx].eval()
        return self

# --- Training Pipeline ---
def train_expert_hard(model, train_loader, expert_idx, epochs=10, lr=0.001):
    """Stage 1: Train one expert on one domain (hard assignment)"""
    trainable = list(model.experts[expert_idx].parameters())
    if any(p.requires_grad for p in model.base.parameters()):
        trainable += list(model.base.parameters())
    optimizer = torch.optim.Adam(trainable, lr=lr)
    model.train()

    for epoch in range(epochs):
        correct = 0; total = 0; total_loss = 0
        for x, y in train_loader:
            output = model.forward_hard(x, expert_idx)
            loss = F.cross_entropy(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            total_loss += loss.item()
        acc = 100.0 * correct / total
        if epoch % 3 == 0 or epoch == epochs - 1:
            print(f"  [E{expert_idx}] Epoch {epoch+1}/{epochs} -- "
                  f"Loss: {total_loss/len(train_loader):.4f}, Acc: {acc:.1f}%")
    return acc

def train_gate_distillation(model, loaders_with_labels, epochs=15, lr=0.001):
    """Stage 2: Gate distillation -- gate learns domain->expert mapping"""
    optimizer = torch.optim.Adam(model.gate.parameters(), lr=lr)
    model.train()

    for epoch in range(epochs):
        correct = 0; total = 0; total_loss = 0
        for expert_idx, loader in loaders_with_labels:
            for x, y in loader:
                feat = model.base(x)
                gate_logits = model.gate(feat)
                target = torch.full((x.size(0),), expert_idx, dtype=torch.long)
                loss = F.cross_entropy(gate_logits, target)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                pred = gate_logits.argmax(dim=-1)
                correct += (pred == target).sum().item()
                total += x.size(0)
                total_loss += loss.item()
        routing_acc = 100.0 * correct / total
        if epoch % 3 == 0 or epoch == epochs - 1:
            print(f"  [Gate] Epoch {epoch+1}/{epochs} -- "
                  f"routing_acc={routing_acc:.1f}%")
    return routing_acc

def evaluate_gated(model, test_loader, domain_name=""):
    model.eval()
    correct = 0; total = 0; gate_counts = [0] * model.n_experts
    with torch.no_grad():
        for x, y in test_loader:
            output, gate_logits, weights = model.forward_gated(x)
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            top_expert = weights.argmax(dim=-1)
            for i in range(model.n_experts):
                gate_counts[i] += (top_expert == i).sum().item()
    acc = 100.0 * correct / total
    gate_pct = [100.0 * c / total for c in gate_counts]
    return acc, gate_pct

# --- Full Pipeline ---
print("=" * 60)
print("BOHN: HARD ASSIGNMENT + GATE DISTILLATION")
print("=" * 60)

model = HardAssignMoE(n_experts=4, n_classes=10)

# Stage 1a: Pre-train base + E0 on MNIST
print("\n--- Stage 1a: Pre-train base + E0 on MNIST ---")
train_expert_hard(model, mnist_train, expert_idx=0, epochs=8, lr=0.001)
model.freeze_base()
# Fine-tune E0
train_expert_hard(model, mnist_train, expert_idx=0, epochs=5, lr=0.0005)
model.freeze_expert(0)

# Stage 1b: Train E1 on Fashion
print("\n--- Stage 1b: Train E1 on Fashion ---")
train_expert_hard(model, fashion_train, expert_idx=1, epochs=10, lr=0.001)
model.freeze_expert(1)

# Stage 2: Gate distillation
print("\n--- Stage 2: Gate Distillation ---")
loaders_2 = [(0, mnist_train), (1, fashion_train)]
train_gate_distillation(model, loaders_2, epochs=15, lr=0.001)

# Stage 3: Add KMNIST -> E2
print("\n--- Stage 3: KMNIST -> E2 ---")
train_expert_hard(model, kmnist_train, expert_idx=2, epochs=10, lr=0.001)
model.freeze_expert(2)

# Retrain gate for 3 domains
loaders_3 = [(0, mnist_train), (1, fashion_train), (2, kmnist_train)]
train_gate_distillation(model, loaders_3, epochs=15, lr=0.001)

# Final evaluation
print("\n--- Final Evaluation ---")
for name, loader in [('MNIST', mnist_test), ('Fashion', fashion_test), ('KMNIST', kmnist_test)]:
    acc, gate_pct = evaluate_gated(model, loader, name)
    print(f"  {name}: {acc:.1f}% | Gate: {['E'+str(i)+':'+f'{g:.1f}%' for i, g in enumerate(gate_pct)]}")
