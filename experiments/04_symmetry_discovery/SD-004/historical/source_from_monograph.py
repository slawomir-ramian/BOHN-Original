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


def flip_horizontal(X):
    img = reshape_images(X)
    return flatten_images(img[:, :, ::-1])


def flip_vertical(X):
    img = reshape_images(X)
    return flatten_images(img[:, ::-1, :])


def rotate_90(X):
    img = reshape_images(X)
    return flatten_images(
        np.rot90(img, k=1, axes=(1, 2))
    )


def rotate_180(X):
    img = reshape_images(X)
    return flatten_images(
        np.rot90(img, k=2, axes=(1, 2))
    )


def random_perm_factory(seed):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N_PIXELS)

    def transform(X):
        return X[:, perm]

    return transform


def sbohn_features(X, transform):
    gX = transform(X)
    S = X + gX
    A = np.abs(X - gX)
    return np.concatenate([S, A], axis=1)


def make_hidden_rotate180_labels(
    X, seed=0, noise=0.10
):
    rng = np.random.default_rng(seed)

    X_rot = rotate_180(X)
    A = np.abs(X - X_rot)

    idx = rng.choice(N_PIXELS, size=12, replace=False)
    weights = rng.uniform(0.5, 1.5, size=len(idx))

    signal = A[:, idx] @ weights
    signal = signal + noise * rng.normal(size=len(X))

    threshold = np.median(signal)
    y = (signal > threshold).astype(int)

    return y


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
    y = make_hidden_rotate180_labels(
        X, seed=seed, noise=0.10
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=seed,
        stratify=y
    )

    candidates = {
        "baseline_x": None,
        "shift_up": shift_up,
        "shift_down": shift_down,
        "shift_left": shift_left,
        "shift_right": shift_right,
        "flip_horizontal": flip_horizontal,
        "flip_vertical": flip_vertical,
        "rotate_90": rotate_90,
        "rotate_180": rotate_180,
    }

    for k in range(n_random):
        candidates[f"random_perm_{k}"] = \
            random_perm_factory(seed * 10000 + k)

    results = []

    for name, transform in candidates.items():
        if transform is None:
            Xtr = X_train
            Xte = X_test
        else:
            Xtr = sbohn_features(X_train, transform)
            Xte = sbohn_features(X_test, transform)

        acc = evaluate(Xtr, Xte, y_train, y_test)

        results.append({
            "candidate": name,
            "accuracy": acc,
            "feature_dim": Xtr.shape[1]
        })

    df = pd.DataFrame(results)
    df = df.sort_values(
        "accuracy", ascending=False
    ).reset_index(drop=True)

    return df


def main():
    seeds = range(30)
    n_random = 20

    all_rows = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        df = run_one(seed, n_random=n_random)
        df["seed"] = seed
        all_rows.append(df)

    results = pd.concat(all_rows, ignore_index=True)

    summary = (
        results
        .groupby("candidate")
        .agg(
            mean_acc=("accuracy", "mean"),
            std_acc=("accuracy", "std"),
            mean_dim=("feature_dim", "mean")
        )
        .reset_index()
        .sort_values("mean_acc", ascending=False)
    )

    baseline_mean = summary[
        summary["candidate"] == "baseline_x"
    ]["mean_acc"].iloc[0]
    random_mean = summary[
        summary["candidate"].str.contains("random_perm")
    ]["mean_acc"].mean()

    summary["gain_vs_baseline"] = \
        summary["mean_acc"] - baseline_mean
    summary["net_vs_random_mean"] = \
        summary["mean_acc"] - random_mean

    print()
    print("======================================")
    print("HIDDEN ROTATE180 SYMMETRY TEST")
    print("======================================")
    print()
    print(f"Seeds: {len(seeds)}")
    print(f"Random permutations per seed: {n_random}")
    print()
    print(f"Baseline mean:     {baseline_mean:.4f}")
    print(f"Random mean:       {random_mean:.4f}")
    print()
    print(summary.to_string(index=False))

    print()
    print("Best candidate per seed:")
    winners = (
        results
        .sort_values(
            ["seed", "accuracy"], ascending=[True, False]
        )
        .groupby("seed")
        .first()
        .reset_index()
    )
    print(winners["candidate"].value_counts().to_string())

    print()
    print("Rank of rotate_180 per seed:")
    ranks = []

    for seed in seeds:
        df_seed = results[
            results["seed"] == seed
        ].copy()
        df_seed = df_seed.sort_values(
            "accuracy", ascending=False
        ).reset_index(drop=True)
        rank = df_seed.index[
            df_seed["candidate"] == "rotate_180"
        ][0] + 1
        ranks.append(rank)

    ranks = np.array(ranks)

    print(f"Mean rank: {ranks.mean():.2f}")
    print(f"Median rank: {np.median(ranks):.2f}")
    print(f"Best rank count: "
          f"{(ranks == 1).sum()} / {len(ranks)}")
    print("Ranks:")
    print(ranks)


if __name__ == "__main__":
    main()
