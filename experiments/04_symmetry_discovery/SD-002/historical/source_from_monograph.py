import numpy as np
import pandas as pd

from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


IMAGE_SIZE = 8
N_PIXELS = 64


def reshape_images(X):
    return X.reshape(-1, IMAGE_SIZE, IMAGE_SIZE)


def flatten_images(X):
    return X.reshape(X.shape[0], -1)


def shift_up(X):
    img = reshape_images(X)
    out = np.zeros_like(img)
    out[:, :-1, :] = img[:, 1:, :]
    return flatten_images(out)


def shift_down(X):
    img = reshape_images(X)
    out = np.zeros_like(img)
    out[:, 1:, :] = img[:, :-1, :]
    return flatten_images(out)


def shift_left(X):
    img = reshape_images(X)
    out = np.zeros_like(img)
    out[:, :, :-1] = img[:, :, 1:]
    return flatten_images(out)


def shift_right(X):
    img = reshape_images(X)
    out = np.zeros_like(img)
    out[:, :, 1:] = img[:, :, :-1]
    return flatten_images(out)


def random_perm_factory(seed):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N_PIXELS)

    def transform(X):
        return X[:, perm]

    return transform


def random_shift_dataset(X, seed=0):
    rng = np.random.default_rng(seed)
    X_new = []

    for row in X:
        img = row.reshape(8, 8)

        dx = rng.integers(-1, 2)
        dy = rng.integers(-1, 2)

        out = np.zeros_like(img)

        for i in range(8):
            for j in range(8):
                ni = i + dx
                nj = j + dy

                if 0 <= ni < 8 and 0 <= nj < 8:
                    out[ni, nj] = img[i, j]

        X_new.append(out.reshape(-1))

    return np.array(X_new)


def sbohn_features(X, transform):
    gX = transform(X)
    S = X + gX
    A = np.abs(X - gX)
    return np.concatenate([S, A], axis=1)


def evaluate(X_train, X_test, y_train, y_test):
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=3000,
            solver="lbfgs"
        )
    )

    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    return accuracy_score(y_test, pred)


def run_one(seed, n_random=20):
    digits = load_digits()

    X = digits.data.astype(np.float32) / 16.0

    # RANDOM LABELS - independent of data
    rng = np.random.default_rng(10_000 + seed)
    y = rng.integers(0, 2, size=len(X))

    X = random_shift_dataset(X, seed=1000 + seed)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=seed,
        stratify=y
    )

    baseline = evaluate(X_train, X_test, y_train, y_test)

    structured = {
        "shift_up": shift_up,
        "shift_down": shift_down,
        "shift_left": shift_left,
        "shift_right": shift_right,
    }

    structured_scores = {}

    for name, transform in structured.items():
        Xtr = sbohn_features(X_train, transform)
        Xte = sbohn_features(X_test, transform)
        structured_scores[name] = evaluate(Xtr, Xte, y_train, y_test)

    random_scores = []

    for k in range(n_random):
        transform = random_perm_factory(seed * 10000 + k)
        Xtr = sbohn_features(X_train, transform)
        Xte = sbohn_features(X_test, transform)
        random_scores.append(evaluate(Xtr, Xte, y_train, y_test))

    random_scores = np.array(random_scores)
    random_mean = random_scores.mean()
    random_best = random_scores.max()

    row = {
        "seed": seed,
        "baseline": baseline,
        "random_mean": random_mean,
        "random_best": random_best,
    }

    for name, score in structured_scores.items():
        row[name] = score
        row[name + "_net_mean"] = score - random_mean
        row[name + "_net_best"] = score - random_best
        row[name + "_gain_baseline"] = score - baseline

    return row


def main():
    seeds = range(30)
    n_random = 20

    rows = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        rows.append(run_one(seed, n_random=n_random))

    df = pd.DataFrame(rows)

    structured_names = [
        "shift_up",
        "shift_down",
        "shift_left",
        "shift_right",
    ]

    print()
    print("======================================")
    print("SBOHN NEGATIVE CONTROL: RANDOM LABELS")
    print("======================================")
    print()
    print(f"Seeds: {len(seeds)}")
    print(f"Random permutations per seed: {n_random}")
    print()

    print("Baseline and random controls:")
    print(f"baseline mean:    "
          f"{df['baseline'].mean():.4f} +/- "
          f"{df['baseline'].std():.4f}")
    print(f"random mean:      "
          f"{df['random_mean'].mean():.4f} +/- "
          f"{df['random_mean'].std():.4f}")
    print(f"random best mean: "
          f"{df['random_best'].mean():.4f} +/- "
          f"{df['random_best'].std():.4f}")
    print()

    summary_rows = []

    for name in structured_names:
        summary_rows.append({
            "candidate": name,
            "acc_mean": df[name].mean(),
            "acc_std": df[name].std(),
            "gain_vs_baseline_mean":
                df[name + "_gain_baseline"].mean(),
            "net_vs_random_mean":
                df[name + "_net_mean"].mean(),
            "net_vs_random_best":
                df[name + "_net_best"].mean(),
            "positive_net_mean_count":
                int((df[name + "_net_mean"] > 0).sum()),
            "positive_net_best_count":
                int((df[name + "_net_best"] > 0).sum()),
        })

    summary = pd.DataFrame(summary_rows)
    summary = summary.sort_values(
        "net_vs_random_mean", ascending=False
    )

    print("Structured candidates:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
