"""
Few-Shot & Continual Learning: BOHN Permutation-Only Adaptation
================================================================
Hypothesis: After full training on MNIST, we can adapt to FashionMNIST
by learning ONLY the Sinkhorn permutation matrix (freezing all weights).
"""
import torch, torch.nn as nn, torch.nn.functional as F
import time, json, gc, numpy as np
from torchvision import datasets, transforms

torch.manual_seed(42)
np.random.seed(42)

# --- Sinkhorn ---
def sinkhorn(log_alpha, n_iter=10, tau=0.1):
    log_alpha = log_alpha / tau
    for _ in range(n_iter):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
    return log_alpha.exp()

# --- Fractal Patch SBOHN v2 ---
class FractalPatchSBOHN(nn.Module):
    def __init__(self, img_size=28, patch_size=7, features_per_patch=16, n_heads=4, n_classes=10):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2
        self.features_per_patch = features_per_patch
        self.n_heads = n_heads
        
        patch_pixels = patch_size * patch_size
        self.patch_encoder = nn.Sequential(
            nn.Linear(patch_pixels, 64), nn.ReLU(),
            nn.Linear(64, features_per_patch)
        )
        
        self.sinkhorn_logits = nn.ParameterList([
            nn.Parameter(torch.randn(self.n_patches, self.n_patches) * 0.1)
            for _ in range(n_heads)
        ])
        
        total_features = features_per_patch * self.n_patches
        self.head = nn.Sequential(
            nn.Linear(total_features * (n_heads + 1), 128), nn.ReLU(),
            nn.Linear(128, n_classes)
        )
    
    def forward(self, x):
        B = x.shape[0]
        p = self.patch_size
        n_side = int(self.n_patches ** 0.5)
        x = x.view(B, 1, n_side * p, n_side * p)
        patches = x.unfold(2, p, p).unfold(3, p, p)
        patches = patches.contiguous().view(B, self.n_patches, p * p)
        
        features = self.patch_encoder(patches)
        
        branches = [features.view(B, -1)]
        for logits in self.sinkhorn_logits:
            P = sinkhorn(logits.unsqueeze(0).expand(B, -1, -1))
            permuted = torch.bmm(P, features)
            branches.append(permuted.view(B, -1))
        
        combined = torch.cat(branches, dim=-1)
        return self.head(combined)

# --- Baselines ---
class SimpleMLP(nn.Module):
    def __init__(self, input_size=784, n_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, n_classes)
        )
    def forward(self, x):
        return self.net(x.view(x.size(0), -1))

class SimpleCNN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.fc = nn.Sequential(
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Linear(128, n_classes)
        )
    def forward(self, x):
        x = x.view(-1, 1, 28, 28)
        x = self.conv(x)
        return self.fc(x.view(x.size(0), -1))

# --- Helpers ---
def get_data(dataset_cls, n_train=None):
    tf = transforms.ToTensor()
    train = dataset_cls('/tmp/data', train=True, download=True, transform=tf)
    test = dataset_cls('/tmp/data', train=False, transform=tf)
    if n_train is not None:
        indices = []
        targets = torch.tensor(train.targets) if isinstance(train.targets, list) else train.targets
        per_class = n_train // 10
        for c in range(10):
            cls_idx = (targets == c).nonzero(as_tuple=True)[0]
            perm = torch.randperm(len(cls_idx))[:per_class]
            indices.extend(cls_idx[perm].tolist())
        train = torch.utils.data.Subset(train, indices)
    train_loader = torch.utils.data.DataLoader(train, batch_size=64, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test, batch_size=256, shuffle=False)
    return train_loader, test_loader

def train_model(model, train_loader, epochs=5, lr=0.001, params=None):
    if params is None:
        params = model.parameters()
    opt = torch.optim.Adam(params, lr=lr)
    model.train()
    for ep in range(epochs):
        for X, y in train_loader:
            X, y = X.float(), y.long()
            opt.zero_grad()
            loss = F.cross_entropy(model(X), y)
            loss.backward()
            opt.step()

def evaluate(model, test_loader):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            pred = model(X.float()).argmax(1)
            correct += (pred == y).sum().item()
            total += len(y)
    return correct / total

# === PHASE 1: Full MNIST training ===
mnist_train, mnist_test = get_data(datasets.MNIST, n_train=3000)
sbohn = FractalPatchSBOHN()
train_model(sbohn, mnist_train, epochs=5)
mnist_perms = [p.data.clone() for p in sbohn.sinkhorn_logits]

mlp = SimpleMLP()
train_model(mlp, mnist_train, epochs=5)

cnn = SimpleCNN()
train_model(cnn, mnist_train, epochs=5)

# === PHASE 2: Few-Shot FashionMNIST ===
# For each n_shots in [10, 50, 100, 500]:
#   - SBOHN perm-only: freeze all, learn only Sinkhorn logits
#   - SBOHN head-only: freeze all, learn only classifier head
#   - SBOHN full-tune: fine-tune all params
#   - MLP/CNN fine-tune from MNIST pretrained
#   - MLP from scratch

# === PHASE 3: Continual Learning ===
# Train perm-only on FashionMNIST -> restore MNIST perms -> check MNIST acc
