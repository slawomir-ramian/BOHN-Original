"""
BOHN Full Experiment Suite -- CPU Edition
All 5 experiments, optimized for CPU (~5 min total)
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

# ============================================================
# DATA: Load all domains (reduced for CPU)
# ============================================================
transform_mnist = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])
transform_cifar = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize(28),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

datasets_dict = {}
for name, ds_class, t in [
    ('MNIST', torchvision.datasets.MNIST, transform_mnist),
    ('Fashion', torchvision.datasets.FashionMNIST, transform_mnist),
    ('KMNIST', torchvision.datasets.KMNIST, transform_mnist),
    ('CIFAR10', torchvision.datasets.CIFAR10, transform_cifar),
]:
    train = ds_class('/tmp/data', train=True, download=True, transform=t)
    test = ds_class('/tmp/data', train=False, download=True, transform=t)
    datasets_dict[name] = (train, test)

def subsample(dataset, n):
    indices = torch.randperm(len(dataset))[:n]
    imgs = torch.stack([dataset[i][0] for i in indices])
    labels = torch.tensor([dataset[i][1] for i in indices])
    return imgs, labels

N_TRAIN = 5000; N_TEST = 1000
data = {}
for name, (train_ds, test_ds) in datasets_dict.items():
    data[name] = {
        'train': subsample(train_ds, N_TRAIN),
        'test': subsample(test_ds, N_TEST)
    }

# ============================================================
# ARCHITECTURES
# ============================================================
class ShallowEncoder(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(784, 512), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(512, dim)
        )
    def forward(self, x):
        return self.net(x)

class DeepEncoder(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(784, 512), nn.ReLU(), nn.BatchNorm1d(512), nn.Dropout(0.1),
            nn.Linear(512, 512), nn.ReLU(), nn.BatchNorm1d(512), nn.Dropout(0.1),
            nn.Linear(512, 384), nn.ReLU(), nn.BatchNorm1d(384), nn.Dropout(0.1),
            nn.Linear(384, dim)
        )
    def forward(self, x):
        return self.net(x)

class SinkhornPerm(nn.Module):
    def __init__(self, dim=256, n_heads=4, tau=0.5, iters=5):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.tau = tau
        self.iters = iters
        self.log_alphas = nn.ParameterList([
            nn.Parameter(torch.randn(self.head_dim, self.head_dim) * 0.01)
            for _ in range(n_heads)
        ])
    
    def sinkhorn(self, log_alpha):
        for _ in range(self.iters):
            log_alpha = log_alpha - torch.logsumexp(
                log_alpha, dim=1, keepdim=True)
            log_alpha = log_alpha - torch.logsumexp(
                log_alpha, dim=0, keepdim=True)
        return torch.exp(log_alpha)
    
    def forward(self, x):
        chunks = x.chunk(self.n_heads, dim=-1)
        out = []
        for i, chunk in enumerate(chunks):
            P = self.sinkhorn(self.log_alphas[i] / self.tau)
            out.append(chunk @ P)
        return torch.cat(out, dim=-1)

class MetaPermGenerator(nn.Module):
    def __init__(self, dim=256, n_heads=4):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.support_encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(784, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU()
        )
        self.perm_generators = nn.ModuleList([
            nn.Sequential(
                nn.Linear(128, 128), nn.ReLU(),
                nn.Linear(128, self.head_dim * self.head_dim)
            ) for _ in range(n_heads)
        ])
        self.sinkhorn_iters = 5
        self.tau = 0.5
    
    def sinkhorn(self, log_alpha):
        for _ in range(self.sinkhorn_iters):
            log_alpha = log_alpha - torch.logsumexp(
                log_alpha, dim=1, keepdim=True)
            log_alpha = log_alpha - torch.logsumexp(
                log_alpha, dim=0, keepdim=True)
        return torch.exp(log_alpha)
    
    def forward(self, support_x, query_x, encoder):
        support_enc = self.support_encoder(support_x)
        context = support_enc.mean(dim=0, keepdim=True)
        query_feat = encoder(query_x)
        chunks = query_feat.chunk(self.n_heads, dim=-1)
        out = []
        for i, chunk in enumerate(chunks):
            log_alpha = self.perm_generators[i](context).view(
                self.head_dim, self.head_dim)
            P = self.sinkhorn(log_alpha / self.tau)
            out.append(chunk @ P)
        return torch.cat(out, dim=-1)

class MoERouter(nn.Module):
    def __init__(self, dim=256, n_experts=4):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(dim, 128), nn.ReLU(),
            nn.Linear(128, n_experts)
        )
    def forward(self, x):
        return F.softmax(self.gate(x), dim=-1)

class BOHNSystem(nn.Module):
    def __init__(self, encoder, dim=256, n_heads=4):
        super().__init__()
        self.encoder = encoder
        self.perm = SinkhornPerm(dim, n_heads)
        self.classifier = nn.Linear(dim, 10)
    
    def forward(self, x):
        h = self.encoder(x)
        h = self.perm(h)
        return self.classifier(h)

class MoESystem(nn.Module):
    def __init__(self, dim=256, n_experts=4, n_heads=4):
        super().__init__()
        self.encoder = DeepEncoder(dim)
        self.router = MoERouter(dim, n_experts)
        self.experts = nn.ModuleList([
            nn.Sequential(SinkhornPerm(dim, n_heads), nn.Linear(dim, 10))
            for _ in range(n_experts)
        ])
    
    def forward(self, x):
        h = self.encoder(x)
        gates = self.router(h)
        expert_outs = torch.stack(
            [exp(h) for exp in self.experts], dim=1)
        return (gates.unsqueeze(-1) * expert_outs).sum(dim=1), gates

# ============================================================
# TRAINING & EVALUATION UTILITIES
# ============================================================
def train_model(model, train_x, train_y, epochs=15, lr=1e-3, bs=128):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(len(train_x))
        for i in range(0, len(train_x), bs):
            idx = perm[i:i+bs]
            out = model(train_x[idx])
            loss = F.cross_entropy(out, train_y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()

def evaluate(model, test_x, test_y, bs=256):
    model.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(test_x), bs):
            out = model(test_x[i:i+bs])
            correct += (out.argmax(1) == test_y[i:i+bs]).sum().item()
    return correct / len(test_y) * 100

# ============================================================
# EXPERIMENT 1: Shallow vs Deep Encoder
# ============================================================
print("=" * 60)
print("EXPERIMENT 1: Shallow vs Deep Encoder")
print("=" * 60)

results_exp1 = {}
for enc_name, EncoderClass in [('Shallow', ShallowEncoder),
                                ('Deep', DeepEncoder)]:
    enc_results = {}
    for domain in ['MNIST', 'Fashion', 'CIFAR10']:
        model = BOHNSystem(EncoderClass(256))
        tx, ty = data[domain]['train']
        ex, ey = data[domain]['test']
        train_model(model, tx, ty, epochs=15)
        acc = evaluate(model, ex, ey)
        enc_results[domain] = acc
        print(f"  {enc_name} on {domain}: {acc:.1f}%")
        del model; gc.collect()
    results_exp1[enc_name] = enc_results

# ============================================================
# EXPERIMENT 2: MoE Multi-Domain Routing
# ============================================================
print("\n" + "=" * 60)
print("EXPERIMENT 2: MoE Multi-Domain Routing")
print("=" * 60)

moe = MoESystem(dim=256, n_experts=4, n_heads=4)
# Combine MNIST + Fashion
mx, my = data['MNIST']['train']
fx, fy = data['Fashion']['train']
combined_x = torch.cat([mx, fx])
combined_y = torch.cat([my, fy])  # same label space 0-9

opt = torch.optim.Adam(moe.parameters(), lr=1e-3)
moe.train()
for ep in range(15):
    perm = torch.randperm(len(combined_x))
    for i in range(0, len(combined_x), 128):
        idx = perm[i:i+128]
        out, gates = moe(combined_x[idx])
        loss = F.cross_entropy(out, combined_y[idx])
        # Load balancing: encourage uniform expert usage
        avg_gates = gates.mean(dim=0)
        balance_loss = (avg_gates * torch.log(avg_gates + 1e-8)).sum()
        total_loss = loss - 0.1 * balance_loss
        opt.zero_grad(); total_loss.backward(); opt.step()

moe.eval()
with torch.no_grad():
    # Per-domain accuracy
    for domain in ['MNIST', 'Fashion']:
        ex, ey = data[domain]['test']
        out, gates = moe(ex)
        acc = (out.argmax(1) == ey).float().mean().item() * 100
        print(f"  {domain}: {acc:.1f}%")
        # Routing distribution
        for exp_i in range(4):
            route_pct = (gates.argmax(1) == exp_i).float().mean().item() * 100
            print(f"    Expert {exp_i}: {route_pct:.1f}%")
    # Mixed
    all_x = torch.cat([data['MNIST']['test'][0], data['Fashion']['test'][0]])
    all_y = torch.cat([data['MNIST']['test'][1], data['Fashion']['test'][1]])
    out, _ = moe(all_x)
    mixed_acc = (out.argmax(1) == all_y).float().mean().item() * 100
    print(f"  Mixed: {mixed_acc:.1f}%")

del moe; gc.collect()

# ============================================================
# EXPERIMENT 3: Cross-Domain Meta-Generator
# ============================================================
print("\n" + "=" * 60)
print("EXPERIMENT 3: Cross-Domain Meta-Generator")
print("=" * 60)

# Train encoder on MNIST
encoder = DeepEncoder(256)
base_model = BOHNSystem(encoder)
train_model(base_model, *data['MNIST']['train'], epochs=10)
encoder.eval()
for p in encoder.parameters():
    p.requires_grad = False

# Train meta-generator on MNIST + Fashion
meta_gen = MetaPermGenerator(dim=256, n_heads=4)
meta_opt = torch.optim.Adam(meta_gen.parameters(), lr=1e-3)
classifier = nn.Linear(256, 10)
cls_opt = torch.optim.Adam(classifier.parameters(), lr=1e-3)

for domain in ['MNIST', 'Fashion']:
    tx, ty = data[domain]['train']
    for ep in range(10):
        perm_idx = torch.randperm(len(tx))
        for i in range(0, len(tx) - 128, 128):
            support_idx = perm_idx[i:i+50]
            query_idx = perm_idx[i+50:i+128]
            support_x = tx[support_idx]
            query_x = tx[query_idx]
            query_y = ty[query_idx]
            
            perm_feat = meta_gen(support_x, query_x, encoder)
            logits = classifier(perm_feat)
            loss = F.cross_entropy(logits, query_y)
            meta_opt.zero_grad()
            cls_opt.zero_grad()
            loss.backward()
            meta_opt.step()
            cls_opt.step()

# Evaluate on all domains
meta_gen.eval(); classifier.eval()
for domain in ['MNIST', 'Fashion', 'KMNIST', 'CIFAR10']:
    tx, ty = data[domain]['train']
    ex, ey = data[domain]['test']
    support_x = tx[:50]
    with torch.no_grad():
        perm_feat = meta_gen(support_x, ex, encoder)
        logits = classifier(perm_feat)
        meta_acc = (logits.argmax(1) == ey).float().mean().item() * 100
        # Random perm baseline
        rand_feat = encoder(ex.view(ex.shape[0], -1))
        rand_logits = classifier(rand_feat)
        rand_acc = (rand_logits.argmax(1) == ey).float().mean().item() * 100
    print(f"  {domain}: Meta-Gen={meta_acc:.1f}%, Random={rand_acc:.1f}%, "
          f"Delta={meta_acc-rand_acc:+.1f}%")

del encoder, meta_gen, classifier, base_model; gc.collect()

# ============================================================
# EXPERIMENT 4: Partial Unfreeze -- Accuracy vs Forgetting
# ============================================================
print("\n" + "=" * 60)
print("EXPERIMENT 4: Partial Unfreeze")
print("=" * 60)

for n_shots in [50, 200, 1000]:
    print(f"\n  --- {n_shots}-shot ---")
    for strategy_name, n_unfreeze in [
        ('Frozen', 0), ('+Last1', 1), ('+Last2', 2),
        ('+Last3', 3), ('All', 99)
    ]:
        # Train fresh encoder on MNIST
        encoder = DeepEncoder(256)
        model = BOHNSystem(encoder)
        train_model(model, *data['MNIST']['train'], epochs=10)
        
        # Freeze encoder
        for p in encoder.parameters():
            p.requires_grad = False
        
        # Selectively unfreeze
        if n_unfreeze > 0:
            layers = [m for m in encoder.net if isinstance(m, nn.Linear)]
            for layer in layers[-n_unfreeze:]:
                for p in layer.parameters():
                    p.requires_grad = True
        
        # New perm + head for Fashion
        perm = SinkhornPerm(256, 4)
        head = nn.Linear(256, 10)
        params = list(perm.parameters()) + list(head.parameters())
        params += [p for p in encoder.parameters() if p.requires_grad]
        opt = torch.optim.Adam(params, lr=1e-3)
        
        fx, fy = data['Fashion']['train']
        idx = torch.randperm(len(fx))[:n_shots]
        few_x, few_y = fx[idx], fy[idx]
        
        # Train
        for ep in range(30):
            h = encoder(few_x)
            h = perm(h)
            logits = head(h)
            loss = F.cross_entropy(logits, few_y)
            opt.zero_grad(); loss.backward(); opt.step()
        
        # Evaluate Fashion
        with torch.no_grad():
            ex, ey = data['Fashion']['test']
            h = encoder(ex); h = perm(h)
            fashion_acc = (head(h).argmax(1) == ey).float().mean().item() * 100
        
        # Evaluate MNIST retention (with original perm+head)
        with torch.no_grad():
            ex, ey = data['MNIST']['test']
            h = encoder(ex); h = model.perm(h)
            mnist_acc = (model.classifier(h).argmax(1) == ey
                         ).float().mean().item() * 100
        
        print(f"    {strategy_name}: Fashion={fashion_acc:.1f}%, "
              f"MNIST={mnist_acc:.1f}%")
        del model, encoder, perm, head; gc.collect()

# ============================================================
# EXPERIMENT 5: Few-Shot Scaling (Frozen Encoder)
# ============================================================
print("\n" + "=" * 60)
print("EXPERIMENT 5: Few-Shot Scaling")
print("=" * 60)

encoder = DeepEncoder(256)
base = BOHNSystem(encoder)
train_model(base, *data['MNIST']['train'], epochs=10)
for p in encoder.parameters():
    p.requires_grad = False

for n_shots in [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]:
    perm = SinkhornPerm(256, 4)
    head = nn.Linear(256, 10)
    opt = torch.optim.Adam(
        list(perm.parameters()) + list(head.parameters()), lr=1e-3)
    
    fx, fy = data['Fashion']['train']
    idx = torch.randperm(len(fx))[:n_shots]
    few_x, few_y = fx[idx], fy[idx]
    
    for ep in range(30):
        h = encoder(few_x); h = perm(h)
        loss = F.cross_entropy(head(h), few_y)
        opt.zero_grad(); loss.backward(); opt.step()
    
    with torch.no_grad():
        ex, ey = data['Fashion']['test']
        h = encoder(ex); h = perm(h)
        acc = (head(h).argmax(1) == ey).float().mean().item() * 100
    print(f"  {n_shots:>5d}-shot: {acc:.1f}%")
    del perm, head; gc.collect()

print("\nAll experiments complete!")
