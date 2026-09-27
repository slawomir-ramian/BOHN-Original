"""
BOHN: Perm + Head Adaptation -- Frozen Encoder, Learned Permutations + Classifier
================================================================================
Hypothesis: By learning ONLY permutations (routing) + head (semantics),
we get strong few-shot AND zero catastrophic forgetting.
"""
import torch, torch.nn as nn, torch.nn.functional as F
import time, json, gc, traceback
from torchvision import datasets, transforms

# -- Sinkhorn --
def sinkhorn(log_alpha, n_iter=10, tau=0.1):
    log_alpha = log_alpha / tau
    for _ in range(n_iter):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
    return log_alpha.exp()

# -- Fractal Patch SBOHN v2 --
class FractalPatchSBOHN(nn.Module):
    def __init__(self, patch_size=7, n_patches=4, features_per_patch=16, n_heads=4, n_classes=10):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.n_heads = n_heads
        self.features_per_patch = features_per_patch
        
        patch_dim = patch_size * patch_size
        
        # Encoder layers (will be frozen)
        self.patch_encoder = nn.Sequential(
            nn.Linear(patch_dim, 64), nn.ReLU(),
            nn.Linear(64, features_per_patch)
        )
        
        # Permutation matrices (will be learned for new tasks)
        self.perm_logits = nn.ParameterList([
            nn.Parameter(torch.randn(n_patches, n_patches) * 0.1) 
            for _ in range(n_heads)
        ])
        
        total_features = n_patches * features_per_patch * n_heads
        
        # Hidden layers (will be frozen)
        self.hidden = nn.Sequential(
            nn.Linear(total_features, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU()
        )
        
        # Classification head (will be learned for new tasks)
        self.classifier = nn.Linear(64, n_classes)
    
    def forward(self, x):
        B = x.shape[0]
        p = self.patch_size
        n = self.n_patches
        
        # Extract patches
        patches = []
        for i in range(2):
            for j in range(2):
                patch = x[:, :, i*p:(i+1)*p, j*p:(j+1)*p].reshape(B, -1)
                patches.append(patch)
        patches = torch.stack(patches, dim=1)
        
        # Encode patches
        encoded = self.patch_encoder(patches)
        
        # Multi-head permutation
        head_outputs = []
        for h in range(self.n_heads):
            P = sinkhorn(self.perm_logits[h].unsqueeze(0).expand(B, -1, -1))
            permuted = torch.bmm(P, encoded)
            combined = (encoded * permuted)
            head_outputs.append(combined.reshape(B, -1))
        
        multi = torch.cat(head_outputs, dim=1)
        features = self.hidden(multi)
        return self.classifier(features)
    
    def get_encoder_params(self):
        return list(self.patch_encoder.parameters()) + list(self.hidden.parameters())
    
    def get_adaptation_params(self):
        params = list(self.classifier.parameters())
        for pl in self.perm_logits:
            params.append(pl)
        return params
    
    def get_perm_only_params(self):
        return [pl for pl in self.perm_logits]
    
    def get_head_only_params(self):
        return list(self.classifier.parameters())
    
    def save_task_params(self):
        return {
            'perm': [p.data.clone() for p in self.perm_logits],
            'head_w': self.classifier.weight.data.clone(),
            'head_b': self.classifier.bias.data.clone()
        }
    
    def load_task_params(self, saved):
        for p, s in zip(self.perm_logits, saved['perm']):
            p.data.copy_(s)
        self.classifier.weight.data.copy_(saved['head_w'])
        self.classifier.bias.data.copy_(saved['head_b'])

# -- Data loading --
def get_data(dataset_cls, n_train=None, n_test=1000):
    transform = transforms.Compose([transforms.ToTensor()])
    train_ds = dataset_cls(root='/tmp/data', train=True, download=True, transform=transform)
    test_ds = dataset_cls(root='/tmp/data', train=False, download=True, transform=transform)
    if n_train:
        train_ds = torch.utils.data.Subset(train_ds, range(min(n_train, len(train_ds))))
    test_ds = torch.utils.data.Subset(test_ds, range(min(n_test, len(test_ds))))
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=128, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=256, shuffle=False)
    return train_loader, test_loader

def evaluate(model, loader):
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for x, y in loader:
            pred = model(x).argmax(1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return 100.0 * correct / total

def train_model(model, loader, epochs, params_to_train=None, lr=0.003):
    if params_to_train is None:
        params_to_train = model.parameters()
    optimizer = torch.optim.Adam(params_to_train, lr=lr)
    model.train()
    for ep in range(epochs):
        for x, y in loader:
            optimizer.zero_grad()
            loss = F.cross_entropy(model(x), y)
            loss.backward()
            optimizer.step()

# -- MLP Baseline --
class MLPBaseline(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(784, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU()
        )
        self.classifier = nn.Linear(64, n_classes)
    def forward(self, x):
        return self.classifier(self.encoder(x))

# ========== EXPERIMENT ==========

# PHASE 1: Full training on MNIST
model = FractalPatchSBOHN()
mnist_train, mnist_test = get_data(datasets.MNIST, n_train=5000)
fmnist_train_full, fmnist_test = get_data(datasets.FashionMNIST, n_train=5000)

train_model(model, mnist_train, epochs=8, lr=0.003)
mnist_task_params = model.save_task_params()
mnist_full_state = {k: v.clone() for k, v in model.state_dict().items()}

mlp = MLPBaseline()
train_model(mlp, mnist_train, epochs=8, lr=0.003)
mlp_full_state = {k: v.clone() for k, v in mlp.state_dict().items()}

# PHASE 2: Few-shot adaptation (6 methods x 6 shot sizes)
# PHASE 3: Continual learning with task switching
# (see full code in /tasklet/agent/home/perm_head_adapt.py)
