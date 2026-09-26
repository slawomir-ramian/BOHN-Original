"""
Learnable SBOHN  5-Step Experimental Pipeline
================================================
Step 1: Temperature $\tau$ with annealing
Step 2: Baselines (Linear, MLP)
Step 3: Multi-layer Sinkhorn (SBOHN-K)
Step 4: Input-dependent P
Step 5: Blind symmetry discovery (symmetry unknown a priori)
"""

import time
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

torch.manual_seed(42)
np.random.seed(42)

# ============================================================
# BUILDING BLOCKS
# ============================================================

class SinkhornOp(nn.Module):
    """Differentiable Sinkhorn normalization with temperature."""
    def __init__(self, n, n_iters=20, tau_init=1.0, learnable_tau=False):
        super().__init__()
        self.n_iters = n_iters
        if learnable_tau:
            self.log_tau = nn.Parameter(torch.tensor(np.log(tau_init)))
        else:
            self.register_buffer('log_tau', torch.tensor(np.log(tau_init)))
    
    @property
    def tau(self):
        return torch.exp(self.log_tau)
    
    def forward(self, M):
        """M: (..., n, n) log-potentials -> doubly stochastic P"""
        P = torch.exp(M / self.tau - torch.max(M / self.tau, dim=-1, keepdim=True).values)
        for _ in range(self.n_iters):
            P = P / (P.sum(dim=-1, keepdim=True) + 1e-9)
            P = P / (P.sum(dim=-2, keepdim=True) + 1e-9)
        return P


def soft_abs(x, eps=1e-5):
    return torch.sqrt(x ** 2 + eps)


def doubly_stochastic_error(P):
    """Diagnostic: how far is P from being doubly stochastic."""
    row_err = (P.sum(dim=-1) - 1).abs().mean().item()
    col_err = (P.sum(dim=-2) - 1).abs().mean().item()
    return row_err, col_err


# ============================================================
# STEP 1: Sinkhorn-SBOHN with temperature annealing
# ============================================================

class SinkhornSBOHN_v1(nn.Module):
    """Single global permutation with temperature."""
    def __init__(self, n_pixels=64, sinkhorn_iters=20, tau_init=1.0):
        super().__init__()
        self.M = nn.Parameter(torch.randn(n_pixels, n_pixels) * 0.02)
        self.sinkhorn = SinkhornOp(n_pixels, sinkhorn_iters, tau_init)
        self.classifier = nn.Linear(n_pixels, 1)
    
    def forward(self, X):
        P = self.sinkhorn(self.M)
        X_perm = X @ P.t()
        A = soft_abs(X - X_perm)
        return self.classifier(A), P


# ============================================================
# STEP 2: Baselines
# ============================================================

class LinearBaseline(nn.Module):
    def __init__(self, n_pixels=64):
        super().__init__()
        self.fc = nn.Linear(n_pixels, 1)
    def forward(self, X):
        return self.fc(X), None

class MLPBaseline(nn.Module):
    def __init__(self, n_pixels=64, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_pixels, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1)
        )
    def forward(self, X):
        return self.net(X), None


# ============================================================
# STEP 3: Multi-layer SBOHN-K (composition of K permutations)
# ============================================================

class SinkhornSBOHN_K(nn.Module):
    """K stacked Sinkhorn permutation layers."""
    def __init__(self, n_pixels=64, K=3, sinkhorn_iters=20, tau_init=0.5):
        super().__init__()
        self.layers = nn.ModuleList()
        for _ in range(K):
            self.layers.append(nn.ModuleDict({
                'M': nn.Module(),  # placeholder
                'sinkhorn': SinkhornOp(n_pixels, sinkhorn_iters, tau_init),
            }))
        # Direct parameter list for M matrices
        self.Ms = nn.ParameterList([
            nn.Parameter(torch.randn(n_pixels, n_pixels) * 0.02) for _ in range(K)
        ])
        self.sinkorns = nn.ModuleList([
            SinkhornOp(n_pixels, sinkhorn_iters, tau_init) for _ in range(K)
        ])
        self.classifier = nn.Linear(n_pixels * K, 1)  # concat features from all layers
    
    def forward(self, X):
        features = []
        Ps = []
        for M_i, sink_i in zip(self.Ms, self.sinkorns):
            P = sink_i(M_i)
            Ps.append(P)
            X_perm = X @ P.t()
            A = soft_abs(X - X_perm)
            features.append(A)
        combined = torch.cat(features, dim=-1)
        return self.classifier(combined), Ps


# ============================================================
# STEP 4: Input-dependent P (attention over permutations)
# ============================================================

class SinkhornSBOHN_InputDep(nn.Module):
    """Input-dependent log-potentials: M(x) = W2 * ReLU(W1 * x)."""
    def __init__(self, n_pixels=64, hidden=32, sinkhorn_iters=20, tau_init=0.5):
        super().__init__()
        self.n_pixels = n_pixels
        # Small network that generates n_pixels*n_pixels log-potentials from input
        self.M_net = nn.Sequential(
            nn.Linear(n_pixels, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_pixels * n_pixels),
        )
        # Scale init to small values
        with torch.no_grad():
            self.M_net[-1].weight.mul_(0.01)
            self.M_net[-1].bias.mul_(0.01)
        
        self.sinkhorn = SinkhornOp(n_pixels, sinkhorn_iters, tau_init)
        self.classifier = nn.Linear(n_pixels, 1)
    
    def forward(self, X):
        B = X.shape[0]
        M = self.M_net(X).view(B, self.n_pixels, self.n_pixels)
        P = self.sinkhorn(M)  # (B, n, n) batch of doubly stochastic matrices
        # Batch matmul: each sample gets its own permutation
        X_perm = torch.bmm(X.unsqueeze(1), P.transpose(-1, -2)).squeeze(1)
        A = soft_abs(X - X_perm)
        return self.classifier(A), P


# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_flip_data(seed=42):
    """Easy task: detect horizontal flip asymmetry (known symmetry)."""
    digits = load_digits()
    X_raw = digits.data
    X_images = X_raw.reshape(-1, 8, 8)
    X_flipped = X_images[:, :, ::-1].reshape(-1, 64)
    
    rng = np.random.default_rng(seed)
    idx = rng.choice(64, size=10, replace=False)
    w = rng.uniform(0.5, 1.5, size=10)
    signal = np.abs(X_raw - X_flipped)[:, idx] @ w
    y = (signal > np.median(signal)).astype(int)
    
    return _split_and_scale(X_raw, y, seed)


def prepare_blind_data(seed=42):
    """
    Step 5: BLIND symmetry discovery.
    Label is based on a HIDDEN geometric transformation (rotation 90 deg),
    NOT horizontal flip. Model must discover the relevant symmetry itself.
    """
    digits = load_digits()
    X_raw = digits.data
    X_images = X_raw.reshape(-1, 8, 8)
    
    # Rotation 90 deg clockwise
    X_rot90 = np.rot90(X_images, k=-1, axes=(1, 2)).reshape(-1, 64)
    
    # Vertical flip
    X_vflip = X_images[:, ::-1, :].reshape(-1, 64)
    
    # Composite: label = f(rot90_asymmetry) XOR g(vflip_asymmetry)
    # This requires discovering BOTH symmetries
    rng = np.random.default_rng(seed)
    
    idx1 = rng.choice(64, size=8, replace=False)
    w1 = rng.uniform(0.3, 1.0, size=8)
    s1 = np.abs(X_raw - X_rot90)[:, idx1] @ w1
    
    idx2 = rng.choice(64, size=8, replace=False)
    w2 = rng.uniform(0.3, 1.0, size=8)
    s2 = np.abs(X_raw - X_vflip)[:, idx2] @ w2
    
    # Label based on whether both signals agree
    y = ((s1 > np.median(s1)).astype(int) == (s2 > np.median(s2)).astype(int)).astype(int)
    
    return _split_and_scale(X_raw, y, seed)


def _split_and_scale(X, y, seed):
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.3, random_state=seed, stratify=y)
    scaler = StandardScaler()
    return (
        torch.tensor(scaler.fit_transform(X_tr), dtype=torch.float32),
        torch.tensor(scaler.transform(X_te), dtype=torch.float32),
        torch.tensor(y_tr, dtype=torch.float32).unsqueeze(1),
        torch.tensor(y_te, dtype=torch.float32).unsqueeze(1),
    )


# ============================================================
# TRAINING LOOP
# ============================================================

def train_model(model, X_tr, X_te, y_tr, y_te, epochs=80, lr=0.01,
                tau_schedule=None, label=""):
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    history = []
    t0 = time.time()
    
    for ep in range(1, epochs + 1):
        # Temperature annealing
        if tau_schedule is not None and hasattr(model, 'sinkhorn'):
            new_tau = tau_schedule(ep, epochs)
            model.sinkhorn.log_tau.data.fill_(np.log(new_tau))
        elif tau_schedule is not None and hasattr(model, 'sinkorns'):
            new_tau = tau_schedule(ep, epochs)
            for s in model.sinkorns:
                s.log_tau.data.fill_(np.log(new_tau))
        
        model.train()
        optimizer.zero_grad()
        out, P = model(X_tr)
        loss = criterion(out, y_tr)
        loss.backward()
        optimizer.step()
        
        model.eval()
        with torch.no_grad():
            pred = model(X_te)[0]
            acc = ((torch.sigmoid(pred) > 0.5).float() == y_te).float().mean().item()
        
        rec = {"epoch": ep, "loss": round(loss.item(), 4), "acc": round(acc, 4)}
        
        # Diagnostics for Sinkhorn models
        if P is not None:
            if isinstance(P, list):
                # Multi-layer: report first layer
                p0 = P[0]
            elif P.dim() == 3:
                # Input-dependent: report mean stats
                p0 = P[0]  # first sample
            else:
                p0 = P
            rec["P_max"] = round(p0.max().item(), 4)
            r_err, c_err = doubly_stochastic_error(p0)
            rec["ds_err"] = round(r_err + c_err, 6)
            if tau_schedule is not None:
                rec["tau"] = round(tau_schedule(ep, epochs), 4)
        
        history.append(rec)
        
        if ep % 20 == 0 or ep == 1:
            extras = ""
            if "P_max" in rec:
                extras += f" | P_max: {rec['P_max']:.4f}"
            if "tau" in rec:
                extras += f" | tau: {rec['tau']:.4f}"
            if "ds_err" in rec:
                extras += f" | DS_err: {rec['ds_err']:.6f}"
            print(f"  [{label}] Ep {ep:3d}/{epochs} | Loss: {rec['loss']:.4f}"
                  f" | Acc: {rec['acc']:.4f}{extras}")
    
    elapsed = time.time() - t0
    best = max(history, key=lambda r: r["acc"])
    return {
        "label": label,
        "best_acc": best["acc"],
        "best_epoch": best["epoch"],
        "final_loss": history[-1]["loss"],
        "time_s": round(elapsed, 2),
        "history": history,
    }


# ============================================================
# TEMPERATURE SCHEDULES
# ============================================================

def cosine_anneal(ep, total, tau_start=1.0, tau_end=0.05):
    progress = ep / total
    return tau_end + 0.5 * (tau_start - tau_end) * (1 + np.cos(np.pi * progress))

def linear_anneal(ep, total, tau_start=1.0, tau_end=0.05):
    return tau_start + (tau_end - tau_start) * (ep / total)


# ============================================================
# MAIN EXPERIMENT
# ============================================================

if __name__ == "__main__":
    results = {}
    
    # --- TASK A: Known symmetry (flip) ---
    print("=" * 70)
    print("TASK A: Known symmetry (horizontal flip)")
    print("=" * 70)
    X_tr, X_te, y_tr, y_te = prepare_flip_data(seed=42)
    print(f"Train: {X_tr.shape}, Test: {X_te.shape}")
    
    # Step 2: Baselines
    print("\n--- Step 2: Baselines ---")
    r = train_model(LinearBaseline(), X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.01, label="Linear")
    results["A_linear"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    r = train_model(MLPBaseline(), X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.005, label="MLP")
    results["A_mlp"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # Step 1: SBOHN v1 without annealing
    print("--- Step 1a: SBOHN v1 (tau=1.0, fixed) ---")
    r = train_model(SinkhornSBOHN_v1(tau_init=1.0), X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.01, label="SBOHN-v1 tau=1.0")
    results["A_sbohn_v1_fixed"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # Step 1: SBOHN v1 with cosine annealing
    print("--- Step 1b: SBOHN v1 (tau cosine 1.0->0.05) ---")
    r = train_model(SinkhornSBOHN_v1(tau_init=1.0), X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.01, tau_schedule=cosine_anneal,
                     label="SBOHN-v1 tau-cos")
    results["A_sbohn_v1_anneal"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # Step 3: Multi-layer SBOHN-K (K=3)
    print("--- Step 3: SBOHN-K (K=3, tau cosine) ---")
    r = train_model(SinkhornSBOHN_K(K=3, tau_init=1.0), X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.005, tau_schedule=cosine_anneal,
                     label="SBOHN-K3")
    results["A_sbohn_K3"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # Step 4: Input-dependent P
    print("--- Step 4: SBOHN Input-Dependent P ---")
    r = train_model(SinkhornSBOHN_InputDep(hidden=32, tau_init=0.5),
                     X_tr, X_te, y_tr, y_te,
                     epochs=80, lr=0.005, label="SBOHN-InpDep")
    results["A_sbohn_inpdep"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # --- TASK B: Blind symmetry discovery (Step 5) ---
    print("=" * 70)
    print("STEP 5 -- TASK B: Blind symmetry discovery (rot90 + vflip)")
    print("=" * 70)
    X_tr2, X_te2, y_tr2, y_te2 = prepare_blind_data(seed=42)
    print(f"Train: {X_tr2.shape}, Test: {X_te2.shape}")
    
    print("\n--- Baseline: Linear ---")
    r = train_model(LinearBaseline(), X_tr2, X_te2, y_tr2, y_te2,
                     epochs=120, lr=0.01, label="Linear-B")
    results["B_linear"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    print("--- Baseline: MLP ---")
    r = train_model(MLPBaseline(hidden=128), X_tr2, X_te2, y_tr2, y_te2,
                     epochs=120, lr=0.003, label="MLP-B")
    results["B_mlp"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    print("--- SBOHN v1 (single perm, tau cosine) ---")
    r = train_model(SinkhornSBOHN_v1(tau_init=1.0), X_tr2, X_te2, y_tr2, y_te2,
                     epochs=120, lr=0.01, tau_schedule=cosine_anneal,
                     label="SBOHN-v1-B")
    results["B_sbohn_v1"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    print("--- SBOHN-K3 (3 permutations, tau cosine) ---")
    r = train_model(SinkhornSBOHN_K(K=3, tau_init=1.0), X_tr2, X_te2, y_tr2, y_te2,
                     epochs=120, lr=0.005, tau_schedule=cosine_anneal,
                     label="SBOHN-K3-B")
    results["B_sbohn_K3"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    print("--- SBOHN Input-Dependent (blind) ---")
    r = train_model(SinkhornSBOHN_InputDep(hidden=48, tau_init=0.5),
                     X_tr2, X_te2, y_tr2, y_te2,
                     epochs=120, lr=0.003, label="SBOHN-InpDep-B")
    results["B_sbohn_inpdep"] = r
    print(f"  >> Best Acc: {r['best_acc']:.4f} @ ep {r['best_epoch']}"
          f" ({r['time_s']}s)\n")
    
    # ============================================================
    # SUMMARY TABLE
    # ============================================================
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Model':<28} {'Task':<8} {'Best Acc':>9} {'Epoch':>6} {'Time':>7}")
    print("-" * 62)
    for key in ["A_linear", "A_mlp", "A_sbohn_v1_fixed",
                "A_sbohn_v1_anneal", "A_sbohn_K3", "A_sbohn_inpdep",
                "B_linear", "B_mlp", "B_sbohn_v1",
                "B_sbohn_K3", "B_sbohn_inpdep"]:
        r = results[key]
        task = "A(flip)" if key.startswith("A") else "B(blind)"
        print(f"{r['label']:<28} {task:<8} {r['best_acc']:>9.4f}"
              f" {r['best_epoch']:>6d} {r['time_s']:>6.2f}s")
    
    # Save full results
    summary = {k: {kk: vv for kk, vv in v.items() if kk != 'history'}
               for k, v in results.items()}
    with open('/tmp/sbohn_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    histories = {k: v['history'] for k, v in results.items()}
    with open('/tmp/sbohn_histories.json', 'w') as f:
        json.dump(histories, f, indent=2)
    
    print("\nResults saved to /tmp/sbohn_results.json")
