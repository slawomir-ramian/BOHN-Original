"""Fractal SBOHN on REAL images  MNIST + Fashion-MNIST"""
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np, json, time, gzip, struct, os
from urllib.request import urlretrieve

torch.manual_seed(42); np.random.seed(42)

# ===============================================
# Data Loading (raw gzip, no torchvision needed)
# ===============================================

print("Loading MNIST...")
mnist_base = 'https://storage.googleapis.com/cvdf-datasets/mnist/'
mnist_files = {
    'tri': 'train-images-idx3-ubyte.gz', 'trl': 'train-labels-idx1-ubyte.gz',
    'tei': 't10k-images-idx3-ubyte.gz',  'tel': 't10k-labels-idx1-ubyte.gz'}
mnist = {}
for k, fn in mnist_files.items():
    p = f'/tmp/mnist_{fn}'
    if not os.path.exists(p):
        urlretrieve(mnist_base + fn, p)
    with gzip.open(p, 'rb') as f:
        if 'i' in k:
            _, n, r, c = struct.unpack('>4I', f.read(16))
            mnist[k] = np.frombuffer(f.read(), np.uint8).reshape(n, 1, r, c).astype(np.float32) / 255.
        else:
            _, n = struct.unpack('>2I', f.read(8))
            mnist[k] = np.frombuffer(f.read(), np.uint8)

print("Loading Fashion-MNIST...")
fmnist_base = 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/'
fmnist_files = {
    'tri': 'train-images-idx3-ubyte.gz', 'trl': 'train-labels-idx1-ubyte.gz',
    'tei': 't10k-images-idx3-ubyte.gz',  'tel': 't10k-labels-idx1-ubyte.gz'}
fmnist = {}
for k, fn in fmnist_files.items():
    p = f'/tmp/fmnist_{fn}'
    if not os.path.exists(p):
        urlretrieve(fmnist_base + fn, p)
    with gzip.open(p, 'rb') as f:
        if 'i' in k:
            _, n, r, c = struct.unpack('>4I', f.read(16))
            fmnist[k] = np.frombuffer(f.read(), np.uint8).reshape(n, 1, r, c).astype(np.float32) / 255.
        else:
            _, n = struct.unpack('>2I', f.read(8))
            fmnist[k] = np.frombuffer(f.read(), np.uint8)

print("Data loaded!")

# ===============================================
# Subset Preparation (pad 28x28 -> 32x32)
# ===============================================

N = 1500    # train samples
NT = 400    # test samples

def prep(data):
    idx = np.random.permutation(len(data['tri']))[:N]
    Xtr = torch.from_numpy(data['tri'][idx])
    Ytr = torch.from_numpy(data['trl'][idx]).long()
    idx = np.random.permutation(len(data['tei']))[:NT]
    Xte = torch.from_numpy(data['tei'][idx])
    Yte = torch.from_numpy(data['tel'][idx]).long()
    # Pad 28x28 -> 32x32
    return F.pad(Xtr, (2, 2, 2, 2)), Ytr, F.pad(Xte, (2, 2, 2, 2)), Yte

mXtr, mYtr, mXte, mYte = prep(mnist)
fXtr, fYtr, fXte, fYte = prep(fmnist)
print(f"MNIST: {mXtr.shape}, FashionMNIST: {fXtr.shape}")

# ===============================================
# Multi-Scale Feature Extraction
# ===============================================

def ms(imgs, L=3):
    """Multi-scale: pool image to [4x4, 8x8, 16x16, 32x32] and flatten"""
    B = imgs.shape[0]
    ss = [4, 8, 16, 32]
    return [F.adaptive_avg_pool2d(imgs, s).reshape(B, -1) for s in ss[:L]]

# ===============================================
# Log-Domain Sinkhorn
# ===============================================

def lsink(la, n=5):
    """Log-domain Sinkhorn: project log-scores to doubly-stochastic matrix"""
    for _ in range(n):
        la = la - torch.logsumexp(la, -1, True)  # row normalize
        la = la - torch.logsumexp(la, -2, True)  # col normalize
    return la.exp()

# ===============================================
# Fractal SBOHN Model
# ===============================================

class FractalSBOHN(nn.Module):
    def __init__(self, feat_dims, n_classes, np_=16, tau=0.1, h=48):
        """
        feat_dims: list of feature dims per level [16, 64, 256, 1024]
        np_: permutation matrix size (16x16)
        tau: Sinkhorn temperature
        h: hidden dim for hypernets
        """
        super().__init__()
        self.nl = len(feat_dims)
        self.np = np_
        self.tau = tau

        self.hn = nn.ModuleList()   # HyperNets: generate P per level
        self.pj = nn.ModuleList()   # Projections: features -> context

        for i, d in enumerate(feat_dims):
            ctx = h if i > 0 else 0  # context from parent level
            self.hn.append(nn.Sequential(
                nn.Linear(d + ctx, h), nn.ReLU(),
                nn.Linear(h, np_ * np_)
            ))
            self.pj.append(nn.Sequential(
                nn.Linear(d, h), nn.ReLU()
            ))

        self.cls = nn.Sequential(
            nn.Linear(h * self.nl, h), nn.ReLU(),
            nn.Linear(h, n_classes)
        )

    def forward(self, feat_list):
        B = feat_list[0].shape[0]
        ctx = None
        projections = []

        for i in range(self.nl):
            f = feat_list[i]

            # HyperNet input: features + context from coarser level
            hi = torch.cat([f, ctx], -1) if ctx is not None else f

            # Generate P via log-domain Sinkhorn
            la = self.hn[i](hi).reshape(B, self.np, self.np)
            P = lsink(la / self.tau, 5)

            # Apply permutation
            fd = f.shape[1]
            if fd >= self.np:
                pm = torch.bmm(P, f[:, :self.np].unsqueeze(-1)).squeeze(-1)
                fa = torch.cat([pm, f[:, self.np:]], -1)
            else:
                pa = F.pad(f, (0, self.np - fd))
                pm = torch.bmm(P, pa.unsqueeze(-1)).squeeze(-1)
                fa = pm[:, :fd]

            # Project to context
            p = self.pj[i](fa)
            projections.append(p)
            ctx = p  # pass down to next level

        return self.cls(torch.cat(projections, -1))

# ===============================================
# MLP Baseline
# ===============================================

class MLP(nn.Module):
    def __init__(self, d_in, n_classes, h=96):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, h), nn.ReLU(),
            nn.Linear(h, h), nn.ReLU(),
            nn.Linear(h, n_classes)
        )

    def forward(self, x):
        return self.net(x)

# ===============================================
# Training & Evaluation
# ===============================================

def train_eval(model, Xtr, Ytr, Xte, Yte, epochs=12, lr=1e-3, fractal=False, L=3):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    BS = 128

    for e in range(epochs):
        model.train()
        perm = np.random.permutation(len(Xtr))
        for s in range(0, len(Xtr), BS):
            ix = perm[s:s+BS]
            xb, yb = Xtr[ix], Ytr[ix]
            logits = model(ms(xb, L)) if fractal else model(xb.reshape(len(xb), -1))
            loss = loss_fn(logits, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        logits = model(ms(Xte, L)) if fractal else model(Xte.reshape(len(Xte), -1))
        acc = (logits.argmax(1) == Yte).float().mean().item()
    return acc, sum(p.numel() for p in model.parameters())

# ===============================================
# Run Experiments
# ===============================================

R = {}

# --- MNIST ---
print("\n" + "=" * 50)
print("MNIST (10 classes, 1500 train)")
print("=" * 50)

experiments_mnist = [
    ('m_Linear',  lambda: nn.Sequential(nn.Linear(1024, 10)),            False, 0),
    ('m_MLP96',   lambda: MLP(1024, 10, 96),                             False, 0),
    ('m_MLP128',  lambda: MLP(1024, 10, 128),                            False, 0),
    ('m_F2L',     lambda: FractalSBOHN([16, 64], 10, 16, 0.1, 48),      True,  2),
    ('m_F3L',     lambda: FractalSBOHN([16, 64, 256], 10, 16, 0.1, 48), True,  3),
    ('m_F3L_h64', lambda: FractalSBOHN([16, 64, 256], 10, 16, 0.1, 64), True,  3),
    ('m_F4L',     lambda: FractalSBOHN([16, 64, 256, 1024], 10, 16, 0.1, 48), True, 4),
    ('m_F4L_h64', lambda: FractalSBOHN([16, 64, 256, 1024], 10, 16, 0.1, 64), True, 4),
]

for nm, model_fn, fractal, L in experiments_mnist:
    t0 = time.time()
    acc, np_ = train_eval(model_fn(), mXtr, mYtr, mXte, mYte, 12, fractal=fractal, L=L)
    dt = time.time() - t0
    print(f"  {nm}: {acc:.1%}  ({np_}p, {dt:.0f}s)")
    R[nm] = {'acc': round(acc, 4), 'params': np_, 'time': round(dt, 1)}

# --- Fashion-MNIST ---
print("\n" + "=" * 50)
print("Fashion-MNIST (10 classes, 1500 train)")
print("=" * 50)

experiments_fmnist = [
    ('f_Linear',  lambda: nn.Sequential(nn.Linear(1024, 10)),            False, 0),
    ('f_MLP96',   lambda: MLP(1024, 10, 96),                             False, 0),
    ('f_MLP128',  lambda: MLP(1024, 10, 128),                            False, 0),
    ('f_F2L',     lambda: FractalSBOHN([16, 64], 10, 16, 0.1, 48),      True,  2),
    ('f_F3L',     lambda: FractalSBOHN([16, 64, 256], 10, 16, 0.1, 48), True,  3),
    ('f_F3L_h64', lambda: FractalSBOHN([16, 64, 256], 10, 16, 0.1, 64), True,  3),
    ('f_F4L',     lambda: FractalSBOHN([16, 64, 256, 1024], 10, 16, 0.1, 48), True, 4),
    ('f_F4L_h64', lambda: FractalSBOHN([16, 64, 256, 1024], 10, 16, 0.1, 64), True, 4),
]

for nm, model_fn, fractal, L in experiments_fmnist:
    t0 = time.time()
    acc, np_ = train_eval(model_fn(), fXtr, fYtr, fXte, fYte, 12, fractal=fractal, L=L)
    dt = time.time() - t0
    print(f"  {nm}: {acc:.1%}  ({np_}p, {dt:.0f}s)")
    R[nm] = {'acc': round(acc, 4), 'params': np_, 'time': round(dt, 1)}

# ===============================================
# Save Results
# ===============================================

with open('/tmp/real_results.json', 'w') as f:
    json.dump(R, f, indent=2)

print("\n\nSUMMARY:")
for ds in ['m', 'f']:
    dsn = 'MNIST' if ds == 'm' else 'Fashion-MNIST'
    print(f"\n  {dsn}:")
    for k in sorted(R.keys()):
        if k.startswith(ds + '_'):
            v = R[k]
            print(f"    {k[2:]}: {v['acc']:.1%} ({v['params']}p)")
print("\nDone!")
