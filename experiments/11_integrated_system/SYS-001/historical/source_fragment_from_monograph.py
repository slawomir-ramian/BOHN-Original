"""
BOHN: 4 Research Directions -- Meta-Perm, MoE Routing, Deeper Encoder, Partial Unfreeze
=======================================================================================
"""
import torch, torch.nn as nn, torch.nn.functional as F
import time, json, gc, traceback
from torchvision import datasets, transforms

torch.manual_seed(42)

# ============================================================
# Shared: Sinkhorn, base SBOHN encoder
# ============================================================
def sinkhorn(log_alpha, n_iters=7):
    for _ in range(n_iters):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
    return log_alpha.exp()

class PatchEncoder(nn.Module):
    """Reusable frozen patch-based encoder"""
    def __init__(self, patch_size=7, n_patches=16, features_per_patch=16, hidden=128):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.features_per_patch = features_per_patch
        self.patch_embed = nn.Linear(patch_size * patch_size, features_per_patch)
        self.encoder = nn.Sequential(
            nn.Linear(n_patches * features_per_patch, hidden),
            nn.ReLU(),
        )
        self.hidden = hidden
    
    def extract_patches(self, x):
        B = x.shape[0]
        x = x.view(B, 1, 28, 28)
        patches = F.unfold(x, self.patch_size, stride=self.patch_size)
        patches = patches.transpose(1, 2)
        return patches

    def forward(self, x, perm_matrix=None):
        patches = self.extract_patches(x)
        patches = self.patch_embed(patches)
        if perm_matrix is not None:
            patches = torch.matmul(perm_matrix.unsqueeze(0), patches)
        flat = patches.reshape(patches.shape[0], -1)
        return self.encoder(flat)

class DeepPatchEncoder(nn.Module):
    """3-layer deep encoder for Direction 3"""
    def __init__(self, patch_size=7, n_patches=16, features_per_patch=16, hidden=128):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.features_per_patch = features_per_patch
        self.patch_embed = nn.Linear(patch_size * patch_size, features_per_patch)
        self.encoder = nn.Sequential(
            nn.Linear(n_patches * features_per_patch, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.hidden = hidden
    
    def extract_patches(self, x):
        B = x.shape[0]
        x = x.view(B, 1, 28, 28)
        patches = F.unfold(x, self.patch_size, stride=self.patch_size)
        patches = patches.transpose(1, 2)
        return patches

    def forward(self, x, perm_matrix=None):
        patches = self.extract_patches(x)
        patches = self.patch_embed(patches)
        if perm_matrix is not None:
            patches = torch.matmul(perm_matrix.unsqueeze(0), patches)
        flat = patches.reshape(patches.shape[0], -1)
        return self.encoder(flat)

class PermGenerator(nn.Module):
    """Takes a support set and generates a permutation matrix"""
    def __init__(self, n_patches=16, feat_dim=16):
        super().__init__()
        self.n_patches = n_patches
        self.support_encoder = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
        )
        self.perm_head = nn.Linear(64, n_patches * n_patches)
    
    def forward(self, support_x):
        feat = self.support_encoder(support_x)
        agg = feat.mean(dim=0)
        log_alpha = self.perm_head(agg).view(self.n_patches, self.n_patches)
        return sinkhorn(log_alpha)

class MoERouter(nn.Module):
    """Routes input to one of N expert (perm+head) pairs"""
    def __init__(self, n_experts=3, n_patches=16, hidden=128, n_classes=10):
        super().__init__()
        self.router = nn.Sequential(
            nn.Linear(784, 64),
            nn.ReLU(),
            nn.Linear(64, n_experts),
        )
        self.log_alphas = nn.ParameterList([
            nn.Parameter(torch.randn(n_patches, n_patches) * 0.01)
            for _ in range(n_experts)
        ])
        self.heads = nn.ModuleList([
            nn.Linear(hidden, n_classes) for _ in range(n_experts)
        ])
        self.n_experts = n_experts
    
    def forward(self, x, encoder):
        route_logits = self.router(x.view(x.shape[0], -1))
        route_weights = F.softmax(route_logits, dim=-1)
        outputs = []
        for i in range(self.n_experts):
            P = sinkhorn(self.log_alphas[i])
            feat = encoder(x, P)
            out = self.heads[i](feat)
            outputs.append(out)
        outputs = torch.stack(outputs, dim=1)
        result = (route_weights.unsqueeze(-1) * outputs).sum(dim=1)
        return result, route_weights
