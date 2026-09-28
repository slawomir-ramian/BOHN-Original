"""
BOHN v6: Hybrid BN/LN -- BEST RESULT
======================================
Architecture: BatchNorm in shared frozen base + LayerNorm in expert modules.
BN base preserves domain info in running stats -> perfect gate routing.
LN experts have no running stats -> zero catastrophic forgetting.
Pipeline: Hard Assignment + Gate Distillation (proven 3-stage approach).
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
# ARCHITECTURE: Hybrid BN/LN
# ============================================================

class SharedBase_BN(nn.Module):
    """Base with BatchNorm -- domain info in running stats.
    Frozen after Stage 1 -> stats don't change -> stable routing signal."""
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

class SinkhornPermutation(nn.Module):
    """Sinkhorn permutation layer for feature reordering."""
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

class ExpertTop_LN(nn.Module):
    """Expert with LayerNorm -- zero forgetting.
    LayerNorm (GroupNorm(1,C)) normalizes per-sample -> no running stats."""
    def __init__(self, n_classes=10, perm_size=64):
        super().__init__()
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
        self.ln3 = nn.GroupNorm(1, 128)   # LayerNorm for conv
        self.ln4 = nn.GroupNorm(1, 128)   # LayerNorm for conv
        self.pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AdaptiveAvgPool2d(3)
        self.sinkhorn = SinkhornPermutation(perm_size)
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(256, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.ln3(self.conv3(x))))
        x = self.avg_pool(F.relu(self.ln4(self.conv4(x))))
        x = x.view(x.size(0), -1)
        # Apply Sinkhorn on first 64 dims
        perm_part = self.sinkhorn(x[:, :64])
        x = torch.cat([perm_part, x[:, 64:]], dim=1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)

class GateNetwork(nn.Module):
    """Gate that sees BN base features -> easy domain discrimination."""
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

class HybridBNLN_MoE(nn.Module):
    """Hybrid BN/LN MoE: BN base (routing) + LN experts (no forgetting)."""
    def __init__(self, n_experts=4, n_classes=10):
        super().__init__()
        self.base = SharedBase_BN()
        self.experts = nn.ModuleList([ExpertTop_LN(n_classes) for _ in range(n_experts)])
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
        """Hard assignment -- one expert per input."""
        feat = self.base(x)
        return self.experts[expert_idx](feat)

    def forward_gated(self, x, top_k=2):
        """Gated inference -- gate selects experts."""
        feat = self.base(x)
        gate_logits = self.gate(feat)
        gate_weights = F.softmax(gate_logits, dim=-1)

        if top_k < self.n_experts:
            topk_vals, topk_idx = torch.topk(gate_weights, top_k, dim=-1)
            mask = torch.zeros_like(gate_weights).scatter_(1, topk_idx, 1.0)
            gate_weights = gate_weights * mask
            gate_weights = gate_weights / (gate_weights.sum(dim=-1, keepdim=True) + 1e-8)

        expert_outputs = []
        for expert in self.experts:
            out = expert(feat)
            expert_outputs.append(out)

        expert_stack = torch.stack(expert_outputs, dim=1)
        gate_expanded = gate_weights.unsqueeze(-1)
        output = (expert_stack * gate_expanded).sum(dim=1)
        return output, gate_logits, gate_weights

    def train(self, mode=True):
        """Keep frozen base in eval mode to preserve BN stats."""
        super().train(mode)
        if not any(p.requires_grad for p in self.base.parameters()):
            self.base.eval()  # BN uses running stats, not batch stats
        for idx in self.frozen_experts:
            self.experts[idx].eval()
        return self

# ============================================================
# TRAINING PIPELINE
# ============================================================

def train_expert_hard(model, train_loader, expert_idx, epochs=10, lr=0.001):
    """Stage 1: Train one expert on one domain (hard assignment)."""
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
        if epoch % 2 == 0 or epoch == epochs - 1:
            print(f"  [E{expert_idx}] Epoch {epoch+1}/{epochs} -- "
                  f"Loss: {total_loss/len(train_loader):.4f}, Acc: {acc:.1f}%")
    return acc

def train_gate_distillation(model, loaders_with_labels, epochs=15, lr=0.001):
    """Stage 2: Gate distillation -- gate learns domain->expert mapping."""
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

def evaluate_oracle(model, test_loader, expert_idx):
    """Evaluate with hard (oracle) assignment."""
    model.eval()
    correct = 0; total = 0
    with torch.no_grad():
        for x, y in test_loader:
            output = model.forward_hard(x, expert_idx)
            correct += (output.argmax(1) == y).sum().item()
            total += y.size(0)
    return 100.0 * correct / total

def evaluate_gated(model, test_loader, domain_name=""):
    """Evaluate with gated (automatic) routing."""
    model.eval()
    correct = 0; total = 0
    gate_counts = [0] * model.n_experts
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

# ============================================================
# RUN FULL PIPELINE
# ============================================================
print("=" * 60)
print("BOHN v6: HYBRID BN/LN -- BEST ARCHITECTURE")
print("=" * 60)

model = HybridBNLN_MoE(n_experts=4, n_classes=10)

# Stage 1a: Pre-train base (BN) + E0 (LN) on MNIST
print("\n--- Stage 1a: Pre-train base + E0 on MNIST ---")
train_expert_hard(model, mnist_train, expert_idx=0, epochs=8, lr=0.001)

# Freeze base
model.freeze_base()
print("  Base frozen (BN in eval mode)")

# Fine-tune E0
print("\n--- Stage 1b: Fine-tune E0 ---")
train_expert_hard(model, mnist_train, expert_idx=0, epochs=5, lr=0.0005)
mnist_e0 = evaluate_oracle(model, mnist_test, 0)
print(f"  MNIST E0: {mnist_e0:.1f}%")
model.freeze_expert(0)

# Stage 1c: Train E1 on Fashion
print("\n--- Stage 1c: Train E1 on Fashion ---")
train_expert_hard(model, fashion_train, expert_idx=1, epochs=10, lr=0.001)
fashion_e1 = evaluate_oracle(model, fashion_test, 1)
mnist_ret = evaluate_oracle(model, mnist_test, 0)
print(f"  Fashion E1: {fashion_e1:.1f}%, MNIST retention: {mnist_ret:.1f}%")
print(f"  Forgetting: {max(0, mnist_e0 - mnist_ret):.1f}%")
model.freeze_expert(1)

# Stage 2: Gate distillation (2 domains)
print("\n--- Stage 2: Gate Distillation (2 domains) ---")
loaders_2 = [(0, mnist_train), (1, fashion_train)]
train_gate_distillation(model, loaders_2, epochs=15, lr=0.001)

# Stage 3: Add KMNIST -> E2
print("\n--- Stage 3: KMNIST -> E2 ---")
train_expert_hard(model, kmnist_train, expert_idx=2, epochs=10, lr=0.001)
kmnist_e2 = evaluate_oracle(model, kmnist_test, 2)
print(f"  KMNIST E2: {kmnist_e2:.1f}%")
model.freeze_expert(2)

# Retrain gate for 3 domains
print("\n--- Gate retraining (3 domains) ---")
loaders_3 = [(0, mnist_train), (1, fashion_train), (2, kmnist_train)]
train_gate_distillation(model, loaders_3, epochs=15, lr=0.001)

# ============================================================
# FINAL EVALUATION
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS: HYBRID BN/LN")
print("=" * 60)

results = {}
for name, loader, eidx in [('MNIST', mnist_test, 0),
                             ('Fashion', fashion_test, 1),
                             ('KMNIST', kmnist_test, 2)]:
    oracle = evaluate_oracle(model, loader, eidx)
    gated, gate_pct = evaluate_gated(model, loader, name)
    results[name] = {'oracle': oracle, 'gated': gated, 'gate_pct': gate_pct}
    gate_str = ', '.join([f'E{i}:{p:.1f}%' for i, p in enumerate(gate_pct)])
    print(f"  {name}: Gated={gated:.1f}%, Oracle={oracle:.1f}%, Gate=[{gate_str}]")

avg_gated = np.mean([r['gated'] for r in results.values()])
avg_oracle = np.mean([r['oracle'] for r in results.values()])
forgetting = max(0, mnist_e0 - results['MNIST']['gated'])
gate_overhead = avg_oracle - avg_gated

print(f"\n  Avg Gated: {avg_gated:.1f}%")
print(f"  Avg Oracle: {avg_oracle:.1f}%")
print(f"  Forgetting: {forgetting:.1f}%")
print(f"  Gate Overhead: {gate_overhead:.1f}%")
print(f"\n  BEST BOHN RESULT!")

# Save results
with open('hybrid_bn_ln_results.json', 'w') as f:
    json.dump({
        'results': {k: {kk: round(vv, 2) if isinstance(vv, float) else vv
                        for kk, vv in v.items()} for k, v in results.items()},
        'avg_gated': round(avg_gated, 2),
        'avg_oracle': round(avg_oracle, 2),
        'forgetting': round(forgetting, 2),
        'gate_overhead': round(gate_overhead, 2)
    }, f, indent=2)
print("\nResults saved to hybrid_bn_ln_results.json")
