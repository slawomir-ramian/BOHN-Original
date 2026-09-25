import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def flip_horizontal(X, img_shape=(8, 8)):
    return np.array([
        x.reshape(img_shape)[:, ::-1].ravel()
        for x in X
    ])

def rotate_180(X, img_shape=(8, 8)):
    return np.array([
        x.reshape(img_shape)[::-1, ::-1].ravel()
        for x in X
    ])

def random_perm(X, seed):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(X.shape[1])
    return X[:, perm]

def sbohn_features(X, transform):
    Xt = transform(X) if callable(transform) \
        else transform
    return np.abs(X - Xt)

def make_labels(X):
    Xr = rotate_180(X)
    asym = np.abs(X - Xr)
    rng = np.random.default_rng(42)
    w = rng.standard_normal(asym.shape[1])
    score = asym @ w
    return (score > np.median(score)).astype(int)

digits = load_digits()
X_all = digits.data.astype(np.float64)
y_all = make_labels(X_all)

C_values = [0.02, 0.05, 0.10, 0.20]

for C in C_values:
    print(f"\n=== C = {C} ===")
    top1_true = 0
    both_top10 = 0
    best_ranks = []
    worst_ranks = []
    accs = []

    for seed in range(10):
        Xtr, Xte, ytr, yte = train_test_split(
            X_all, y_all, test_size=0.3,
            random_state=seed
        )
        blocks = {}
        blocks["flip_horizontal"] = \
            sbohn_features(Xtr, flip_horizontal)
        blocks["rotate_180"] = \
            sbohn_features(Xtr, rotate_180)
        for k in range(97):
            name = f"rand_{k}"
            blocks[name] = sbohn_features(
                Xtr,
                lambda X, s=seed*10000+k:
                    random_perm(X, s)
            )

        Phi_tr = np.hstack(
            [blocks[n] for n in sorted(blocks)]
        )

        blocks_te = {}
        blocks_te["flip_horizontal"] = \
            sbohn_features(Xte, flip_horizontal)
        blocks_te["rotate_180"] = \
            sbohn_features(Xte, rotate_180)
        for k in range(97):
            name = f"rand_{k}"
            blocks_te[name] = sbohn_features(
                Xte,
                lambda X, s=seed*10000+k:
                    random_perm(X, s)
            )
        Phi_te = np.hstack(
            [blocks_te[n] for n in sorted(blocks_te)]
        )

        clf = LogisticRegression(
            C=C, penalty="l1",
            solver="saga", max_iter=5000
        )
        clf.fit(Phi_tr, ytr)
        acc = clf.score(Phi_te, yte)
        accs.append(acc)

        names = sorted(blocks.keys())
        W = clf.coef_
        importances = {}
        for i, n in enumerate(names):
            sl = slice(i * 64, (i + 1) * 64)
            importances[n] = \
                np.sum(np.abs(W[:, sl]))

        ranking = sorted(
            importances, key=importances.get,
            reverse=True
        )
        true_set = {
            "flip_horizontal", "rotate_180"
        }
        true_ranks = [
            ranking.index(t) + 1
            for t in true_set
        ]
        best_ranks.append(min(true_ranks))
        worst_ranks.append(max(true_ranks))

        if ranking[0] in true_set:
            top1_true += 1
        top10 = set(ranking[:10])
        if true_set <= top10:
            both_top10 += 1

    print(f"  Accuracy:          "
          f"{np.mean(accs):.4f}")
    print(f"  Top1 True:         "
          f"{top1_true}/10")
    print(f"  Both True Top10:   "
          f"{both_top10}/10")
    print(f"  Mean Best Rank:    "
          f"{np.mean(best_ranks):.1f}")
    print(f"  Mean Worst Rank:   "
          f"{np.mean(worst_ranks):.1f}")
