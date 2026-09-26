"""
Tests D & E  lighter versions (K=2, smaller hidden, fewer epochs)
"""
import torch, torch.nn as nn, torch.optim as optim, numpy as np, json, time
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

torch.manual_seed(42); np.random.seed(42)

# Load previous results
RESULTS = {}

def log_sinkhorn(la, n_iters=15, tau=1.0):
    la = la / tau
    for _ in range(n_iters):
        la = la - torch.logsumexp(la, dim=-1, keepdim=True)
        la = la - torch.logsumexp(la, dim=-2, keepdim=True)
    return torch.exp(la)

def entropy_of_P(P):
    return -(P * torch.log(P + 1e-10)).sum(dim=-1).mean()

def prepare_task_B(seed=42):
    digits = load_digits(); X_raw = digits.data
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
    return (torch.tensor(sc.fit_transform(Xtr), dtype=torch.float32),
            torch.tensor(sc.transform(Xte), dtype=torch.float32),
            torch.tensor(ytr, dtype=torch.float32).unsqueeze(1),
            torch.tensor(yte, dtype=torch.float32).unsqueeze(1))

X_train, X_test, y_train, y_test = prepare_task_B()
criterion = nn.BCEWithLogitsLoss()

# ============================================================
# TEST D: Full Stack -- InpDep K=2 (lighter)
# ============================================================
print("=" * 70)
print("TEST D: Full Stack InpDep K=2 + LogDomain + Entropy + Ortho")
print("=" * 70)

class FullStackSBOHN(nn.Module):
    def __init__(self, n_pixels=64, K=2, hidden=24,
                 sinkhorn_iters=12, epsilon=1e-5):
        super().__init__()
        self.K = K; self.sinkhorn_iters = sinkhorn_iters
        self.epsilon = epsilon; self.n_pixels = n_pixels
        self.encoder = nn.Sequential(
            nn.Linear(n_pixels, hidden), nn.ReLU())
        self.heads = nn.ModuleList([
            nn.Linear(hidden, n_pixels*n_pixels) for _ in range(K)])
        self.classifier = nn.Linear(n_pixels*K, 1)
    
    def forward(self, X, tau=0.5):
        h = self.encoder(X)
        all_feats, all_Ps = [], []
        for k in range(self.K):
            la = self.heads[k](h).view(-1, self.n_pixels, self.n_pixels)
            P = log_sinkhorn(la, self.sinkhorn_iters, tau)
            Xp = torch.bmm(X.unsqueeze(1), P.transpose(1,2)).squeeze(1)
            all_feats.append(torch.sqrt((X - Xp)**2 + self.epsilon))
            all_Ps.append(P)
        return self.classifier(torch.cat(all_feats, dim=1)), all_Ps
    
    def entropy_loss(self, Ps):
        return sum(entropy_of_P(P) for P in Ps) / len(Ps)
    
    def ortho_loss(self, Ps):
        if len(Ps) < 2: return torch.tensor(0.0)
        I = torch.eye(self.n_pixels).unsqueeze(0).expand(
            Ps[0].shape[0],-1,-1)
        return (torch.bmm(Ps[0], Ps[1].transpose(1,2))
                - I).norm(dim=(1,2)).mean()

# Use mini-batches to reduce memory
def train_fullstack(label, le, lo, sched):
    if sched == "cos":
        tau_fn = lambda ep: 0.1 + 0.5*0.4*(1+np.cos(np.pi*ep/50))
    else:
        tau_fn = lambda ep: 0.3
    
    torch.manual_seed(42)
    model = FullStackSBOHN(K=2, hidden=24, sinkhorn_iters=10)
    opt = optim.Adam(model.parameters(), lr=0.003)
    hist = []
    t0 = time.time()
    bs = 256  # mini-batch
    
    for epoch in range(1, 51):
        tau = tau_fn(epoch)
        model.train()
        # Mini-batch training
        perm = torch.randperm(X_train.shape[0])
        for start in range(0, X_train.shape[0], bs):
            idx = perm[start:start+bs]
            opt.zero_grad()
            out, Ps = model(X_train[idx], tau=tau)
            total = criterion(out, y_train[idx])
            if le > 0: total = total + le * model.entropy_loss(Ps)
            if lo > 0: total = total + lo * model.ortho_loss(Ps)
            if torch.isnan(total):
                return label, {"acc": 0, "entropy": 99,
                               "pmax": 0, "nan": True}
            total.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        
        if epoch % 10 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                # Eval in mini-batches too
                all_preds = []
                for start in range(0, X_test.shape[0], bs):
                    pr, _ = model(X_test[start:start+bs], tau=tau)
                    all_preds.append(pr)
                preds = torch.cat(all_preds)
                acc = ((torch.sigmoid(preds)>0.5).float()
                       ==y_test).float().mean().item()
            hist.append({"ep": epoch, "acc": acc, "tau": round(tau,3)})
    
    elapsed = time.time() - t0
    f = hist[-1]
    # Final eval with entropy/pmax
    model.eval()
    with torch.no_grad():
        _, Pt = model(X_test[:bs], tau=tau_fn(50))
        ent = model.entropy_loss(Pt).item()
        pmx = sum(P.max(dim=-1).values.max(dim=-1).values.mean().item()
                  for P in Pt)/2
    
    return label, {"acc": f["acc"], "entropy": ent, "pmax": pmx,
                   "time": round(elapsed,1), "history": hist}

test_d = {}
for label, le, lo, sched in [
    ("no_reg_anneal", 0, 0, "cos"),
    ("ent0.1_ort0.1_anneal", 0.1, 0.1, "cos"),
    ("ent0.5_ort0.1_anneal", 0.5, 0.1, "cos"),
    ("ent0.1_ort0.1_fixed", 0.1, 0.1, "fix"),
]:
    lbl, res = train_fullstack(label, le, lo, sched)
    test_d[lbl] = res
    print(f"  [{lbl:<25}] Acc={res['acc']:.4f}"
          f" Ent={res.get('entropy',0):.3f}"
          f" Pmax={res.get('pmax',0):.3f}"
          f" ({res.get('time',0):.0f}s)")

RESULTS["test_d"] = test_d


# ============================================================
# TEST E: Algebraic Analysis of Entropy-Regularized Model
# ============================================================
print("\n" + "=" * 70)
print("TEST E: Algebraic Analysis (Entropy-Regularized Global K=3)")
print("=" * 70)

class SBOHNLogK(nn.Module):
    def __init__(self, n_pixels=64, K=3, sinkhorn_iters=25, epsilon=1e-5):
        super().__init__()
        self.K = K; self.sinkhorn_iters = sinkhorn_iters
        self.epsilon = epsilon
        self.M_list = nn.ParameterList([
            nn.Parameter(torch.randn(n_pixels, n_pixels)*0.02)
            for _ in range(K)
        ])
        self.classifier = nn.Linear(n_pixels*K, 1)
    
    def get_Ps(self, tau=1.0):
        return [log_sinkhorn(M, self.sinkhorn_iters, tau)
                for M in self.M_list]
    
    def forward(self, X, tau=1.0):
        Ps = self.get_Ps(tau)
        feats = [torch.sqrt((X - torch.matmul(X, P.t()))**2
                            + self.epsilon) for P in Ps]
        return self.classifier(torch.cat(feats, dim=1)), Ps
    
    def entropy_loss(self, Ps):
        return sum(entropy_of_P(P) for P in Ps) / len(Ps)
    def ortho_loss(self, Ps):
        loss = torch.tensor(0.0); c = 0
        for i in range(len(Ps)):
            for j in range(i+1, len(Ps)):
                loss = loss + (torch.mm(Ps[i], Ps[j].t())
                               - torch.eye(64)).norm()
                c += 1
        return loss / max(c,1)

torch.manual_seed(42)
model_alg = SBOHNLogK(K=3, sinkhorn_iters=30)
opt_alg = optim.Adam(model_alg.parameters(), lr=0.01)

for epoch in range(1, 101):
    tau = 0.05 + 0.5*0.95*(1+np.cos(np.pi*epoch/100))
    model_alg.train(); opt_alg.zero_grad()
    out, Ps = model_alg(X_train, tau=tau)
    total = (criterion(out, y_train) + 0.5*model_alg.entropy_loss(Ps)
             + 0.1*model_alg.ortho_loss(Ps))
    total.backward(); opt_alg.step()

model_alg.eval()
with torch.no_grad():
    preds_alg, Ps_final = model_alg(X_test, tau=0.05)
    alg_acc = ((torch.sigmoid(preds_alg)>0.5).float()
               ==y_test).float().mean().item()
print(f"  Model accuracy (ent0.5+ort0.1, 100ep): {alg_acc:.4f}")

def perm_mat(idx):
    n = len(idx); P = torch.zeros(n, n)
    for i, j in enumerate(idx): P[i,j] = 1.0
    return P

ix = np.arange(64).reshape(8, 8)
syms = {
    "identity": ix.flatten(), "h_flip": ix[:, ::-1].flatten(),
    "v_flip": ix[::-1, :].flatten(),
    "rot90": np.rot90(ix, 1).flatten(),
    "rot180": np.rot90(ix, 2).flatten(),
    "rot270": np.rot90(ix, 3).flatten(),
    "diag": ix.T.flatten(),
    "anti_diag": np.rot90(ix, 1)[:, ::-1].flatten(),
}
P_syms = {n: perm_mat(p) for n, p in syms.items()}

test_e = {"matrices": [], "model_acc": alg_acc}

for k, P in enumerate(Ps_final):
    pk = f"P{k+1}"
    pmx = P.max().item(); ent = entropy_of_P(P).item()
    
    # Hard (argmax) permutation
    P_hard = torch.zeros_like(P)
    for row in range(64): P_hard[row, P[row].argmax()] = 1.0
    is_perm = ((P_hard.sum(0)==1).all().item()
               and (P_hard.sum(1)==1).all().item())
    n_unique = len(P_hard.argmax(dim=1).unique())
    
    # Distances
    dists_soft = {n: round((P - Ps).norm().item(), 3)
                  for n, Ps in P_syms.items()}
    dists_hard = {n: round((P_hard - Ps).norm().item(), 3)
                  for n, Ps in P_syms.items()}
    
    sorted_soft = sorted(dists_soft.items(), key=lambda x: x[1])
    sorted_hard = sorted(dists_hard.items(), key=lambda x: x[1])
    
    print(f"\n  {pk}: P_max={pmx:.4f}, Entropy={ent:.3f},"
          f" valid_perm={is_perm}, unique={n_unique}/64")
    print(f"    Soft closest: {sorted_soft[0][0]}({sorted_soft[0][1]}),"
          f" {sorted_soft[1][0]}({sorted_soft[1][1]})")
    print(f"    Hard closest: {sorted_hard[0][0]}({sorted_hard[0][1]}),"
          f" {sorted_hard[1][0]}({sorted_hard[1][1]})")
    
    # Powers of hard P
    Pk = P_hard.clone(); I = torch.eye(64); powers = {}
    for n in range(2, 13):
        Pk = torch.mm(Pk, P_hard)
        powers[f"P^{n}"] = round((Pk - I).norm().item(), 3)
    min_pow = min(powers.items(), key=lambda x: x[1])
    print(f"    Min power P^n approx I: {min_pow[0]}"
          f" (dist={min_pow[1]})")
    
    # Cycle structure of hard P
    perm_indices = P_hard.argmax(dim=1).numpy()
    visited = set(); cycles = []
    for start in range(64):
        if start in visited: continue
        cycle = []; curr = start
        while curr not in visited:
            visited.add(curr); cycle.append(curr)
            curr = int(perm_indices[curr])
        cycles.append(len(cycle))
    cycles.sort(reverse=True)
    cycle_str = "+".join(str(c) for c in cycles[:10])
    if len(cycles) > 10:
        cycle_str += f"+...({len(cycles)} total)"
    print(f"    Cycle structure: [{cycle_str}]")
    
    test_e["matrices"].append({
        "pmax": pmx, "entropy": ent,
        "is_valid_perm": is_perm, "n_unique": n_unique,
        "closest_soft": sorted_soft[:4],
        "closest_hard": sorted_hard[:4],
        "min_power": {"power": min_pow[0], "dist": min_pow[1]},
        "cycle_structure": cycles,
        "all_dists_hard": dists_hard, "powers": powers
    })

# Pairwise products
print(f"\n  Pairwise products:")
hard_Ps = []
for P in Ps_final:
    Ph = torch.zeros_like(P)
    for row in range(64): Ph[row, P[row].argmax()] = 1.0
    hard_Ps.append(Ph)

test_e["pairwise"] = []
for i in range(3):
    for j in range(i+1, 3):
        prod = torch.mm(hard_Ps[i], hard_Ps[j].t())
        min_d, min_n = float('inf'), ""
        for name, Ps in P_syms.items():
            d = (prod - Ps).norm().item()
            if d < min_d: min_d = d; min_n = name
        print(f"    P{i+1} P{j+1}^T: closest={min_n} ({min_d:.1f})")
        test_e["pairwise"].append({
            "pair": f"P{i+1}P{j+1}T",
            "closest": min_n, "dist": round(min_d,1)
        })

    # Also check P_i * P_j (composition)
    for j in range(3):
        if i == j: continue
        comp = torch.mm(hard_Ps[i], hard_Ps[j])
        min_d, min_n = float('inf'), ""
        for name, Ps in P_syms.items():
            d = (comp - Ps).norm().item()
            if d < min_d: min_d = d; min_n = name
        if min_d < 2.0:
            print(f"    P{i+1} P{j+1} approx {min_n}!"
                  f" (dist={min_d:.3f})")

RESULTS["test_e"] = test_e

with open("/tmp/sbohn_logdomain_results.json", "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)

print("\nAll results saved.")
