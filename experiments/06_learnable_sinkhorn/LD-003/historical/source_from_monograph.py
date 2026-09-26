"""
Learnable SBOHN  Log-Domain Sinkhorn + Entropy Regularization (Optimized)
==========================================================================
Vectorized batched log-domain Sinkhorn for speed.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import time
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

torch.manual_seed(42)
np.random.seed(42)

RESULTS = {}

# ============================================================
# CORE: Log-Domain Sinkhorn (vectorized for batches)
# ============================================================

def log_sinkhorn(log_alpha, n_iters=20, tau=1.0):
    """Log-domain Sinkhorn. Works on 2D [n,n] or 3D [B,n,n]."""
    log_alpha = log_alpha / tau
    for _ in range(n_iters):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=-2, keepdim=True)
    return torch.exp(log_alpha)


def naive_sinkhorn(M, n_iters=20, tau=1.0):
    P = torch.exp(M / tau - torch.max(M / tau, dim=-1, keepdim=True).values)
    for _ in range(n_iters):
        P = P / (P.sum(dim=-1, keepdim=True) + 1e-9)
        P = P / (P.sum(dim=-2, keepdim=True) + 1e-9)
    return P


def entropy_of_P(P):
    """Row-wise entropy. Works on 2D or 3D."""
    return -(P * torch.log(P + 1e-10)).sum(dim=-1).mean()


# ============================================================
# DATA
# ============================================================

def prepare_task_B(seed=42):
    digits = load_digits()
    X_raw = digits.data
    X_imgs = X_raw.reshape(-1, 8, 8)
    rng = np.random.default_rng(seed)
    X_rot = np.rot90(X_imgs, k=1, axes=(1, 2)).reshape(-1, 64)
    idx1 = rng.choice(64, size=8, replace=False)
    w1 = rng.uniform(0.5, 1.5, size=8)
    s1 = np.abs(X_raw - X_rot)[:, idx1] @ w1
    X_vf = X_imgs[:, ::-1, :].reshape(-1, 64)
    idx2 = rng.choice(64, size=6, replace=False)
    w2 = rng.uniform(0.3, 1.0, size=6)
    s2 = np.abs(X_raw - X_vf)[:, idx2] @ w2
    signal = 0.6 * s1 + 0.4 * s2
    y = (signal > np.median(signal)).astype(int)
    Xtr, Xte, ytr, yte = train_test_split(
        X_raw, y, test_size=0.3, random_state=seed, stratify=y)
    sc = StandardScaler()
    return (
        torch.tensor(sc.fit_transform(Xtr), dtype=torch.float32),
        torch.tensor(sc.transform(Xte), dtype=torch.float32),
        torch.tensor(ytr, dtype=torch.float32).unsqueeze(1),
        torch.tensor(yte, dtype=torch.float32).unsqueeze(1),
    )

X_train, X_test, y_train, y_test = prepare_task_B()
criterion = nn.BCEWithLogitsLoss()

# ============================================================
# TEST A: Log-domain vs Naive Stability
# ============================================================
print("=" * 70)
print("TEST A: Log-Domain vs Naive Sinkhorn -- Numerical Stability")
print("=" * 70)

test_a = {}
M = torch.randn(64, 64) * 0.5

for tau in [1.0, 0.5, 0.1, 0.05, 0.01, 0.005, 0.001]:
    try:
        P_n = naive_sinkhorn(M, 30, tau)
        n_ok = not torch.isnan(P_n).any().item()
        n_ds = float((P_n.sum(1)-1).abs().mean()) if n_ok else float('inf')
        n_mx = float(P_n.max()) if n_ok else float('nan')
    except:
        n_ok, n_ds, n_mx = False, float('inf'), float('nan')
    try:
        P_l = log_sinkhorn(M, 30, tau)
        l_ok = not torch.isnan(P_l).any().item()
        l_ds = float((P_l.sum(1)-1).abs().mean()) if l_ok else float('inf')
        l_mx = float(P_l.max()) if l_ok else float('nan')
    except:
        l_ok, l_ds, l_mx = False, float('inf'), float('nan')
    
    print(f"  tau={tau:<6} | Naive: "
          f"{'ok' if n_ok else 'NaN':<8} DS={n_ds:.4f} Pmax={n_mx:.3f}"
          f" | Log: {'ok' if l_ok else 'NaN':<8} DS={l_ds:.6f} Pmax={l_mx:.3f}")
    test_a[str(tau)] = {
        "naive_ok": n_ok, "naive_ds": n_ds, "naive_pmax": n_mx,
        "log_ok": l_ok, "log_ds": l_ds, "log_pmax": l_mx
    }

RESULTS["test_a"] = test_a


# ============================================================
# TEST B: InpDep + tau Annealing (Log-Domain) -- vectorized
# ============================================================
print("\n" + "=" * 70)
print("TEST B: Input-Dependent + tau Annealing (Log-Domain)")
print("=" * 70)

class InpDepLogSinkhorn(nn.Module):
    def __init__(self, n_pixels=64, hidden=32, sinkhorn_iters=15, epsilon=1e-5):
        super().__init__()
        self.sinkhorn_iters = sinkhorn_iters
        self.epsilon = epsilon
        self.n_pixels = n_pixels
        self.hypernet = nn.Sequential(
            nn.Linear(n_pixels, hidden), nn.ReLU(),
            nn.Linear(hidden, n_pixels * n_pixels)
        )
        self.classifier = nn.Linear(n_pixels, 1)
    
    def forward(self, X, tau=0.5):
        B = X.shape[0]
        log_alpha = self.hypernet(X).view(B, self.n_pixels, self.n_pixels)
        P = log_sinkhorn(log_alpha, self.sinkhorn_iters, tau)  # [B, n, n]
        X_perm = torch.bmm(X.unsqueeze(1), P.transpose(1, 2)).squeeze(1)
        A = torch.sqrt((X - X_perm) ** 2 + self.epsilon)
        return self.classifier(A), P

test_b = {}
for label, tau_fn in [
    ("fixed_0.5", lambda ep: 0.5),
    ("cos_1->0.05", lambda ep: 0.05 + 0.5*0.95*(1+np.cos(np.pi*ep/60))),
    ("cos_0.5->0.1", lambda ep: 0.1 + 0.5*0.4*(1+np.cos(np.pi*ep/60))),
    ("lin_0.5->0.05", lambda ep: max(0.05, 0.5 - 0.45*ep/60)),
    ("lin_0.5->0.1", lambda ep: max(0.1, 0.5 - 0.4*ep/60)),
]:
    torch.manual_seed(42)
    model = InpDepLogSinkhorn()
    opt = optim.Adam(model.parameters(), lr=0.005)
    hist = []
    nan_hit = False
    t0 = time.time()
    
    for epoch in range(1, 61):
        tau = tau_fn(epoch)
        model.train(); opt.zero_grad()
        out, P = model(X_train, tau=tau)
        loss = criterion(out, y_train)
        if torch.isnan(loss): nan_hit = True; break
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        
        if epoch % 15 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                pr, Pt = model(X_test, tau=tau)
                acc = ((torch.sigmoid(pr)>0.5).float()==y_test).float().mean().item()
                pmx = Pt.max(dim=-1).values.max(dim=-1).values.mean().item()
            hist.append({
                "ep": epoch, "acc": acc, "pmax": pmx,
                "tau": round(tau,3), "loss": round(float(loss),4)
            })
    
    elapsed = time.time() - t0
    final = hist[-1] if hist else {"acc":0, "pmax":0}
    status = (f"NaN at ep {epoch}" if nan_hit
              else f"Acc={final['acc']:.4f} Pmax={final['pmax']:.3f}")
    print(f"  [{label:<15}] {status} ({elapsed:.1f}s)")
    test_b[label] = {
        "nan": nan_hit, "final_acc": final.get("acc",0),
        "final_pmax": final.get("pmax",0), "history": hist,
        "time": round(elapsed,1)
    }

RESULTS["test_b"] = test_b


# ============================================================
# TEST C: Entropy Regularization
# ============================================================
print("\n" + "=" * 70)
print("TEST C: Entropy Regularization on P (Global K=3)")
print("=" * 70)

class SBOHNLogK(nn.Module):
    def __init__(self, n_pixels=64, K=3, sinkhorn_iters=20, epsilon=1e-5):
        super().__init__()
        self.K = K; self.sinkhorn_iters = sinkhorn_iters
        self.epsilon = epsilon
        self.M_list = nn.ParameterList([
            nn.Parameter(torch.randn(n_pixels, n_pixels)*0.02) for _ in range(K)
        ])
        self.classifier = nn.Linear(n_pixels*K, 1)
    
    def get_Ps(self, tau=1.0):
        return [log_sinkhorn(M, self.sinkhorn_iters, tau) for M in self.M_list]
    
    def forward(self, X, tau=1.0):
        Ps = self.get_Ps(tau)
        feats = []
        for P in Ps:
            Xp = torch.matmul(X, P.t())
            feats.append(torch.sqrt((X - Xp)**2 + self.epsilon))
        return self.classifier(torch.cat(feats, dim=1)), Ps
    
    def entropy_loss(self, Ps):
        return sum(entropy_of_P(P) for P in Ps) / len(Ps)
    
    def ortho_loss(self, Ps):
        loss = torch.tensor(0.0); c = 0
        for i in range(len(Ps)):
            for j in range(i+1, len(Ps)):
                loss = loss + (torch.mm(Ps[i], Ps[j].t())
                               - torch.eye(Ps[i].shape[0])).norm()
                c += 1
        return loss / max(c, 1)

test_c = {}
for label, lam_ent, lam_ort in [
    ("no_reg", 0, 0), ("ent_0.01", 0.01, 0), ("ent_0.1", 0.1, 0),
    ("ent_0.5", 0.5, 0), ("ent_1.0", 1.0, 0),
    ("ent0.1+ort0.1", 0.1, 0.1), ("ent0.5+ort0.1", 0.5, 0.1),
]:
    torch.manual_seed(42)
    model = SBOHNLogK(K=3, sinkhorn_iters=25)
    opt = optim.Adam(model.parameters(), lr=0.01)
    tau_fn = lambda ep: 0.05 + 0.5*0.95*(1+np.cos(np.pi*ep/60))
    
    for epoch in range(1, 61):
        tau = tau_fn(epoch)
        model.train(); opt.zero_grad()
        out, Ps = model(X_train, tau=tau)
        total = criterion(out, y_train)
        if lam_ent > 0: total = total + lam_ent * model.entropy_loss(Ps)
        if lam_ort > 0: total = total + lam_ort * model.ortho_loss(Ps)
        total.backward(); opt.step()
    
    model.eval()
    with torch.no_grad():
        pr, Ps_t = model(X_test, tau=0.05)
        acc = ((torch.sigmoid(pr)>0.5).float()==y_test).float().mean().item()
        ent = model.entropy_loss(Ps_t).item()
        pmx = sum(P.max().item() for P in Ps_t)/3
    
    print(f"  [{label:<18}] Acc={acc:.4f} | Entropy={ent:.3f} | P_max={pmx:.3f}")
    test_c[label] = {"acc": acc, "entropy": ent, "pmax": pmx}

RESULTS["test_c"] = test_c

with open("/tmp/sbohn_logdomain_results.json", "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)

print("\nAll results saved.")
