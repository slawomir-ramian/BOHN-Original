"""Patch SBOHN  'Permutation Transformer'
Instead of permuting pixels, permute patches of the image.
Like ViT but with Sinkhorn permutation instead of attention.
"""
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np, json, time, gzip, struct, os
from urllib.request import urlretrieve

# --- Data loading (MNIST + Fashion-MNIST) ---
def load_mnist_raw(path, kind='train'):
    labels_path = os.path.join(path, f'{kind}-labels-idx1-ubyte.gz')
    images_path = os.path.join(path, f'{kind}-images-idx3-ubyte.gz')
    with gzip.open(labels_path,'rb') as f:
        _ = struct.unpack('>II', f.read(8)); labels = np.frombuffer(f.read(), dtype=np.uint8)
    with gzip.open(images_path,'rb') as f:
        _ = struct.unpack('>IIII', f.read(16)); images = np.frombuffer(f.read(), dtype=np.uint8).reshape(-1,28,28)
    return images, labels

def get_data(name, n_train=2000, n_test=500):
    if name == 'mnist':
        base = 'https://ossci-datasets.s3.amazonaws.com/mnist/'
        path = '/tmp/mnist_data'
    else:
        base = 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/'
        path = '/tmp/fmnist_data'
    os.makedirs(path, exist_ok=True)
    for f in ['train-images-idx3-ubyte.gz','train-labels-idx1-ubyte.gz',
              't10k-images-idx3-ubyte.gz','t10k-labels-idx1-ubyte.gz']:
        fp = os.path.join(path, f)
        if not os.path.exists(fp):
            print(f"  Downloading {f}...")
            urlretrieve(base + f, fp)
    X_tr, y_tr = load_mnist_raw(path, 'train')
    X_te, y_te = load_mnist_raw(path, 't10k')
    # Pad 28x28 -> 32x32
    X_tr = np.pad(X_tr, ((0,0),(2,2),(2,2)), mode='constant')
    X_te = np.pad(X_te, ((0,0),(2,2),(2,2)), mode='constant')
    # Subsample
    idx_tr = np.random.choice(len(X_tr), n_train, replace=False)
    idx_te = np.random.choice(len(X_te), n_test, replace=False)
    X_tr = torch.tensor(X_tr[idx_tr], dtype=torch.float32) / 255.0
    y_tr = torch.tensor(y_tr[idx_tr], dtype=torch.long)
    X_te = torch.tensor(X_te[idx_te], dtype=torch.float32) / 255.0
    y_te = torch.tensor(y_te[idx_te], dtype=torch.long)
    return X_tr, y_tr, X_te, y_te

# --- Log-domain Sinkhorn ---
def log_sinkhorn(log_alpha, n_iter=10):
    for _ in range(n_iter):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
    return log_alpha.exp()

# --- Patch SBOHN: Permutation Transformer ---
class PatchSBOHN(nn.Module):
    """
    1. Split image into patches
    2. Flatten each patch to a vector
    3. Apply Sinkhorn doubly-stochastic P to permute patch ORDER
    4. Classify from permuted patch sequence
    """
    def __init__(self, img_size=32, patch_size=8, n_classes=10, 
                 tau=0.3, n_sinkhorn=10, input_dep=False, 
                 hidden_dim=64, n_heads=1):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2  # 16 for 32/8
        self.patch_dim = patch_size * patch_size  # 64 for 8x8
        self.tau = tau
        self.n_sinkhorn = n_sinkhorn
        self.input_dep = input_dep
        self.n_heads = n_heads
        N = self.n_patches  # 16
        
        # Patch embedding (like ViT)
        self.patch_embed = nn.Linear(self.patch_dim, hidden_dim)
        
        # Positional embedding
        self.pos_embed = nn.Parameter(torch.randn(1, N, hidden_dim) * 0.02)
        
        if input_dep:
            # Hypernet: from patch sequence -> P logits
            self.hyper = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, N * N * n_heads)
            )
        else:
            self.log_alpha = nn.Parameter(torch.randn(n_heads, N, N) * 0.1)
        
        # Multi-head: apply n_heads permutations, concat results
        self.classifier = nn.Sequential(
            nn.Linear(N * hidden_dim * n_heads, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, n_classes)
        )
        
    def extract_patches(self, x):
        """x: (B, H, W) -> (B, n_patches, patch_dim)"""
        B, H, W = x.shape
        ps = self.patch_size
        x = x.reshape(B, H//ps, ps, W//ps, ps)
        x = x.permute(0, 1, 3, 2, 4)  # (B, nH, nW, ps, ps)
        x = x.reshape(B, self.n_patches, self.patch_dim)
        return x
    
    def forward(self, x):
        B = x.shape[0]
        N = self.n_patches
        
        # 1. Extract & embed patches
        patches = self.extract_patches(x)  # (B, N, patch_dim)
        z = self.patch_embed(patches) + self.pos_embed  # (B, N, hidden)
        
        # 2. Get permutation matrix
        if self.input_dep:
            ctx = z.mean(dim=1)  # (B, hidden)
            logits = self.hyper(ctx)  # (B, N*N*n_heads)
            logits = logits.reshape(B, self.n_heads, N, N)
            P = log_sinkhorn(logits / self.tau, self.n_sinkhorn)
        else:
            P = log_sinkhorn(
                self.log_alpha.unsqueeze(0).expand(B,-1,-1,-1) / self.tau, 
                self.n_sinkhorn
            )
        
        # 3. Apply permutation to patch sequence (per head)
        head_outputs = []
        for h in range(self.n_heads):
            Ph = P[:, h]  # (B, N, N)
            z_perm = torch.bmm(Ph, z)  # (B, N, hidden)
            head_outputs.append(z_perm.reshape(B, -1))
        
        combined = torch.cat(head_outputs, dim=-1)
        
        # 4. Classify
        return self.classifier(combined)

# --- Baselines ---
class MLPBaseline(nn.Module):
    def __init__(self, input_dim=1024, hidden=128, n_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden, n_classes)
        )
    def forward(self, x):
        return self.net(x.reshape(x.shape[0], -1))

class PatchMLPBaseline(nn.Module):
    """MLP that also uses patch embedding (fair comparison)"""
    def __init__(self, img_size=32, patch_size=8, hidden_dim=64, n_classes=10):
        super().__init__()
        n_patches = (img_size // patch_size) ** 2
        patch_dim = patch_size * patch_size
        self.patch_size = patch_size
        self.n_patches = n_patches
        self.patch_dim = patch_dim
        self.patch_embed = nn.Linear(patch_dim, hidden_dim)
        self.pos_embed = nn.Parameter(torch.randn(1, n_patches, hidden_dim) * 0.02)
        self.classifier = nn.Sequential(
            nn.Linear(n_patches * hidden_dim, hidden_dim * 2), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, n_classes)
        )
    def forward(self, x):
        B, H, W = x.shape
        ps = self.patch_size
        patches = x.reshape(B, H//ps, ps, W//ps, ps) \
                   .permute(0,1,3,2,4) \
                   .reshape(B, self.n_patches, self.patch_dim)
        z = self.patch_embed(patches) + self.pos_embed
        return self.classifier(z.reshape(B, -1))

# --- Training ---
def train_model(model, X_tr, y_tr, X_te, y_te, epochs=20, lr=1e-3, label=""):
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    n_params = sum(p.numel() for p in model.parameters())
    best_acc = 0
    losses = []
    
    t0 = time.time()
    for ep in range(epochs):
        model.train()
        idx = torch.randperm(len(X_tr))
        ep_loss = 0
        bs = 128
        for i in range(0, len(X_tr), bs):
            batch_idx = idx[i:i+bs]
            logits = model(X_tr[batch_idx])
            loss = F.cross_entropy(logits, y_tr[batch_idx])
            opt.zero_grad(); loss.backward(); opt.step()
            ep_loss += loss.item()
        sched.step()
        losses.append(ep_loss / (len(X_tr) // bs))
        
        model.eval()
        with torch.no_grad():
            acc = (model(X_te).argmax(1) == y_te).float().mean().item()
            best_acc = max(best_acc, acc)
    
    elapsed = time.time() - t0
    print(f"  {label:30s} | acc={best_acc:.1%} | params={n_params:>7,d} | {elapsed:.1f}s")
    return {'label': label, 'acc': best_acc, 'params': n_params, 
            'losses': losses, 'time': elapsed}

# --- Main ---
np.random.seed(42); torch.manual_seed(42)
all_results = {}

for dataset in ['mnist', 'fmnist']:
    print(f"\n{'='*60}")
    print(f"  Dataset: {dataset.upper()}")
    print(f"{'='*60}")
    X_tr, y_tr, X_te, y_te = get_data(dataset, n_train=2000, n_test=500)
    print(f"  Train: {X_tr.shape}, Test: {X_te.shape}")
    
    results = []
    
    # Baselines
    results.append(train_model(
        MLPBaseline(1024, 128), X_tr, y_tr, X_te, y_te, 
        epochs=25, label="MLP-128 (flat)"))
    results.append(train_model(
        PatchMLPBaseline(32, 8, 64), X_tr, y_tr, X_te, y_te, 
        epochs=25, label="PatchMLP-64 (no perm)"))
    
    # Patch SBOHN variants
    for tau in [0.5, 0.3]:
        results.append(train_model(
            PatchSBOHN(32, 8, tau=tau, input_dep=False, hidden_dim=64, n_heads=1),
            X_tr, y_tr, X_te, y_te, epochs=25, 
            label=f"PatchSBOHN global $\tau$={tau}"))
    
    results.append(train_model(
        PatchSBOHN(32, 8, tau=0.3, input_dep=True, hidden_dim=64, n_heads=1),
        X_tr, y_tr, X_te, y_te, epochs=25, 
        label="PatchSBOHN InpDep 1H $\tau$=0.3"))
    results.append(train_model(
        PatchSBOHN(32, 8, tau=0.1, input_dep=True, hidden_dim=64, n_heads=1),
        X_tr, y_tr, X_te, y_te, epochs=25, 
        label="PatchSBOHN InpDep 1H $\tau$=0.1"))
    
    # Multi-head
    results.append(train_model(
        PatchSBOHN(32, 8, tau=0.3, input_dep=True, hidden_dim=64, n_heads=4),
        X_tr, y_tr, X_te, y_te, epochs=25, 
        label="PatchSBOHN InpDep 4H $\tau$=0.3"))
    results.append(train_model(
        PatchSBOHN(32, 8, tau=0.1, input_dep=True, hidden_dim=64, n_heads=4),
        X_tr, y_tr, X_te, y_te, epochs=25, 
        label="PatchSBOHN InpDep 4H $\tau$=0.1"))
    
    # Deeper hidden
    results.append(train_model(
        PatchSBOHN(32, 8, tau=0.1, input_dep=True, hidden_dim=128, n_heads=4),
        X_tr, y_tr, X_te, y_te, epochs=25, lr=5e-4, 
        label="PatchSBOHN InpDep 4H h128 $\tau$=0.1"))
    
    all_results[dataset] = results

# Save
with open('/tmp/patch_results.json','w') as f:
    json.dump({k: [{'label':r['label'],'acc':r['acc'],'params':r['params'],
                     'losses':r['losses']} for r in v] 
               for k,v in all_results.items()}, f, indent=2)
print("\n[OK] All done! Results saved.")
