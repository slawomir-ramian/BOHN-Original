"""
BOHN Integrated System: MoE + Meta-Generator + Frozen Encoder
=============================================================
Scenario: System learns MNIST -> then receives 50 FashionMNIST examples
-> meta-generator creates a new expert -> router automatically routes inputs
-> zero forgetting on MNIST
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import time, json, gc
from torchvision import datasets, transforms

torch.manual_seed(42)

# ===================== ARCHITECTURE =====================

class SinkhornLayer(nn.Module):
    def __init__(self, size, tau=0.1, iters=7):
        super().__init__()
        self.log_alpha = nn.Parameter(torch.randn(size, size) * 0.01)
        self.tau = tau
        self.iters = iters
    
    def forward(self, x):
        M = self.log_alpha / self.tau
        for _ in range(self.iters):
            M = M - torch.logsumexp(M, dim=1, keepdim=True)
            M = M - torch.logsumexp(M, dim=0, keepdim=True)
        P = torch.exp(M)
        return x @ P

class FrozenEncoder(nn.Module):
    def __init__(self, input_dim=784, hidden=128, feat_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, feat_dim), nn.ReLU()
        )
    def forward(self, x):
        return self.net(x)

class Expert(nn.Module):
    def __init__(self, feat_dim=64, n_classes=10):
        super().__init__()
        self.perm = SinkhornLayer(feat_dim)
        self.head = nn.Linear(feat_dim, n_classes)
    def forward(self, x):
        return self.head(self.perm(x))
    def param_count(self):
        return sum(p.numel() for p in self.parameters())

class MetaPermGenerator(nn.Module):
    def __init__(self, feat_dim=64, hidden=128):
        super().__init__()
        self.feat_dim = feat_dim
        self.task_encoder = nn.Sequential(
            nn.Linear(feat_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.perm_decoder = nn.Linear(hidden, feat_dim * feat_dim)
    
    def forward(self, support_features):
        task_emb = support_features.mean(dim=0, keepdim=True)
        h = self.task_encoder(task_emb)
        log_alpha = self.perm_decoder(h).view(self.feat_dim, self.feat_dim)
        return log_alpha * 0.01

class TaskRouter(nn.Module):
    def __init__(self, feat_dim=64, n_experts=4):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(feat_dim, 32), nn.ReLU(),
            nn.Linear(32, n_experts)
        )
    def forward(self, x):
        return F.softmax(self.gate(x), dim=-1)

class BOHNIntegratedSystem(nn.Module):
    def __init__(self, feat_dim=64, max_experts=4, n_classes=10):
        super().__init__()
        self.feat_dim = feat_dim
        self.encoder = FrozenEncoder(feat_dim=feat_dim)
        self.meta_gen = MetaPermGenerator(feat_dim=feat_dim)
        self.router = TaskRouter(feat_dim=feat_dim, n_experts=max_experts)
        self.experts = nn.ModuleList()
        self.max_experts = max_experts
        self.n_classes = n_classes
    
    def add_expert(self):
        expert = Expert(self.feat_dim, self.n_classes)
        self.experts.append(expert)
        return len(self.experts) - 1
    
    def add_expert_from_meta(self, support_features):
        expert = Expert(self.feat_dim, self.n_classes)
        with torch.no_grad():
            log_alpha = self.meta_gen(support_features)
            expert.perm.log_alpha.data = log_alpha
        self.experts.append(expert)
        return len(self.experts) - 1
    
    def freeze_encoder(self):
        for p in self.encoder.parameters():
            p.requires_grad = False
    
    def forward(self, x, expert_idx=None):
        features = self.encoder(x)
        if expert_idx is not None:
            return self.experts[expert_idx](features)
        gates = self.router(features.detach())
        n_active = len(self.experts)
        outputs = []
        for i in range(n_active):
            outputs.append(self.experts[i](features))
        stacked = torch.stack(outputs, dim=1)
        gate_weights = gates[:, :n_active].unsqueeze(-1)
        mixed = (stacked * gate_weights).sum(dim=1)
        return mixed
