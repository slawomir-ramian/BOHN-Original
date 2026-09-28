"""
BOHN: Sparse MoE + Gate Specialization Loss
=============================================
Building on Partial Unfreeze + MoE, adding:
1. Top-k sparse gating (top-2 of 4 experts active)
2. Gate specialization loss (negative entropy -> sharper routing)
3. Load balancing loss (prevent expert collapse)
4. Comparison: dense gate vs sparse gate vs sparse+specialization

CPU-optimized: smaller data, fewer epochs, same architecture.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import numpy as np
import json
import time
from collections import defaultdict

torch.manual_seed(42)
np.random.seed(42)

# --- Data Loading (CPU-optimized) ---
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

# --- Shared Encoder (Frozen first 2 layers) ---
class SharedEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2))
        self.layer2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2))

    def forward(self, x):
        return self.layer2(self.layer1(x))

# --- Expert Module (own top layers + Sinkhorn perm + head) ---
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
        return (flat @ P).view_as(x) if flat.size(1) == P.size(0) else x

class Expert(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.layer3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2))
        self.layer4 = nn.Sequential(
            nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1))
        self.sinkhorn = SinkhornPermutation(128)
        self.head = nn.Linear(128, n_classes)

    def forward(self, x):
        h = self.layer4(self.layer3(x))
        h = h.view(h.size(0), -1)
        h = self.sinkhorn(h)
        return self.head(h), h

# --- Gate Variants ---
class DenseGate(nn.Module):
    def __init__(self, input_dim, n_experts):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, n_experts))

    def forward(self, x):
        flat = x.view(x.size(0), -1)
        logits = self.gate(flat)
        weights = F.softmax(logits, dim=-1)
        return weights, logits

class SparseGate(nn.Module):
    def __init__(self, input_dim, n_experts, top_k=2):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, n_experts))
        self.top_k = top_k
        self.n_experts = n_experts

    def forward(self, x):
        flat = x.view(x.size(0), -1)
        logits = self.gate(flat)
        topk_vals, topk_idx = torch.topk(logits, self.top_k, dim=-1)
        mask = torch.zeros_like(logits).scatter_(1, topk_idx, 1.0)
        sparse_logits = logits * mask + (1 - mask) * (-1e9)
        weights = F.softmax(sparse_logits, dim=-1)
        return weights, logits

# --- Loss Components ---
def gate_specialization_loss(gate_logits, temperature=1.0):
    probs = F.softmax(gate_logits / temperature, dim=-1)
    entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1)
    return entropy.mean()

def load_balancing_loss(gate_logits, n_experts):
    probs = F.softmax(gate_logits, dim=-1)
    expert_load = probs.mean(dim=0)
    target = torch.ones(n_experts) / n_experts
    return F.mse_loss(expert_load, target)

# --- Sparse MoE System ---
class SparseMoESystem(nn.Module):
    def __init__(self, n_experts=4, gate_type='sparse', top_k=2,
                 spec_loss_weight=0.1, balance_loss_weight=0.1):
        super().__init__()
        self.encoder = SharedEncoder()
        self.experts = nn.ModuleList([Expert() for _ in range(n_experts)])
        self.n_experts = n_experts
        self.gate_type = gate_type
        self.spec_loss_weight = spec_loss_weight
        self.balance_loss_weight = balance_loss_weight

        gate_input_dim = 64 * 7 * 7
        if gate_type == 'dense':
            self.gate = DenseGate(gate_input_dim, n_experts)
        else:
            self.gate = SparseGate(gate_input_dim, n_experts, top_k=top_k)

        for p in self.encoder.parameters():
            p.requires_grad = False

    def forward(self, x, return_gate_info=False):
        with torch.no_grad():
            shared_feat = self.encoder(x)
        weights, gate_logits = self.gate(shared_feat)

        expert_outputs = []
        for i, expert in enumerate(self.experts):
            logits_i, _ = expert(shared_feat)
            expert_outputs.append(logits_i)

        expert_stack = torch.stack(expert_outputs, dim=1)
        weights_expanded = weights.unsqueeze(-1)
        output = (expert_stack * weights_expanded).sum(dim=1)

        if return_gate_info:
            return output, gate_logits, weights
        return output

    def compute_aux_losses(self, gate_logits):
        spec = gate_specialization_loss(gate_logits)
        balance = load_balancing_loss(gate_logits, self.n_experts)
        return self.spec_loss_weight * spec, self.balance_loss_weight * balance

# --- Training ---
def train_domain(model, train_loader, epochs=8, lr=0.001, domain_name="",
                 use_spec_loss=True, freeze_other_experts=None):
    if freeze_other_experts is not None:
        for i, expert in enumerate(model.experts):
            for p in expert.parameters():
                p.requires_grad = (i not in freeze_other_experts)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=lr)
    model.train()

    for epoch in range(epochs):
        total_loss = 0; correct = 0; total = 0; gate_entropy_sum = 0
        for x, y in train_loader:
            output, gate_logits, weights = model(x, return_gate_info=True)
            task_loss = F.cross_entropy(output, y)
            loss = task_loss
            if use_spec_loss:
                spec_loss, bal_loss = model.compute_aux_losses(gate_logits)
                loss = task_loss + spec_loss + bal_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            probs = F.softmax(gate_logits, dim=-1)
            entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1).mean()
            gate_entropy_sum += entropy.item()

        acc = 100.0 * correct / total
        avg_entropy = gate_entropy_sum / len(train_loader)
        if epoch % 3 == 0 or epoch == epochs - 1:
            print(f"  [{domain_name}] Epoch {epoch+1}/{epochs} -- "
                  f"Loss: {total_loss/len(train_loader):.4f}, "
                  f"Acc: {acc:.1f}%, Gate H: {avg_entropy:.3f}")
    return acc

def evaluate(model, test_loader):
    model.eval()
    correct = 0; total = 0; gate_weights_all = []
    with torch.no_grad():
        for x, y in test_loader:
            output, gate_logits, weights = model(x, return_gate_info=True)
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
            gate_weights_all.append(weights)
    acc = 100.0 * correct / total
    all_weights = torch.cat(gate_weights_all, dim=0)
    avg_weights = all_weights.mean(dim=0).numpy()
    return acc, avg_weights

def get_gate_stats(model, test_loader, domain_name):
    model.eval()
    all_weights = []; all_topk = []
    with torch.no_grad():
        for x, y in test_loader:
            _, gate_logits, weights = model(x, return_gate_info=True)
            all_weights.append(weights)
            topk = weights.argmax(dim=-1)
            all_topk.append(topk)
    weights = torch.cat(all_weights, dim=0)
    topk = torch.cat(all_topk, dim=0)
    expert_counts = [(topk == i).float().mean().item() for i in range(model.n_experts)]
    avg_weights = weights.mean(dim=0).numpy()
    entropy = -(weights * (weights + 1e-8).log()).sum(dim=-1).mean().item()
    return {
        'domain': domain_name, 'expert_traffic': expert_counts,
        'avg_weights': avg_weights.tolist(), 'avg_entropy': entropy,
        'dominant_expert': int(np.argmax(expert_counts)),
        'dominance_ratio': max(expert_counts)
    }
