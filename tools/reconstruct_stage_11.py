#!/usr/bin/env python3
"""Jawna rekonstrukcja faz pominiętych w listingach 58 i 59."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from copy import deepcopy
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bohn_original.adaptation_continual import (  # noqa: E402
    FewShotSBOHN,
    PermHeadMLP,
    PermHeadSBOHN,
    SimpleCNN,
    SimpleMLP,
    parameter_count,
    parameter_count_of,
    select_trainable,
)

PROTOCOL = "STAGE_11_RECONSTRUCTION_V1"
SEED = 42


def seed_all(seed: int = SEED) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def loader(dataset, batch_size: int, shuffle: bool, seed: int = SEED) -> DataLoader:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, generator=generator, num_workers=0)


def first_subset(dataset, count: int) -> Subset:
    return Subset(dataset, range(min(count, len(dataset))))


def balanced_subset(dataset, count: int, seed: int = SEED) -> Subset:
    targets = torch.as_tensor(dataset.targets)
    per_class = max(1, count // 10)
    generator = torch.Generator().manual_seed(seed)
    indices = []
    for label in range(10):
        candidates = torch.nonzero(targets == label, as_tuple=True)[0]
        order = torch.randperm(len(candidates), generator=generator)[:per_class]
        indices.extend(candidates[order].tolist())
    return Subset(dataset, indices)


def evaluate(model, data_loader: DataLoader) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in data_loader:
            predictions = model(images.float()).argmax(1)
            correct += int((predictions == labels).sum())
            total += len(labels)
    return 100.0 * correct / total


def train(model, data_loader: DataLoader, epochs: int, lr: float,
          parameters=None) -> None:
    selected = list(model.parameters()) if parameters is None else select_trainable(model, parameters)
    optimizer = torch.optim.Adam(selected, lr=lr)
    for _ in range(epochs):
        model.train()
        for images, labels in data_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(images.float()), labels.long())
            loss.backward()
            optimizer.step()


def load_datasets(data_root: Path):
    try:
        from torchvision import datasets, transforms
    except Exception as exc:
        raise RuntimeError(
            "Nie można zaimportować torchvision. Uruchom ponownie SETUP_STAGE_11.ps1."
        ) from exc
    transform = transforms.ToTensor()
    mnist_train = datasets.MNIST(data_root, train=True, download=True, transform=transform)
    mnist_test = datasets.MNIST(data_root, train=False, download=True, transform=transform)
    fashion_train = datasets.FashionMNIST(data_root, train=True, download=True, transform=transform)
    fashion_test = datasets.FashionMNIST(data_root, train=False, download=True, transform=transform)
    return mnist_train, mnist_test, fashion_train, fashion_test


def protocol_perm_head(data_root: Path) -> dict:
    """Uzupełnij komentarze PHASE 2/3 z listingu 58."""
    seed_all()
    mnist_train, mnist_test, fashion_train, fashion_test = load_datasets(data_root)
    mnist_train_loader = loader(first_subset(mnist_train, 5000), 128, True)
    mnist_test_loader = loader(first_subset(mnist_test, 1000), 256, False)
    fashion_test_loader = loader(first_subset(fashion_test, 1000), 256, False)

    model = PermHeadSBOHN()
    train(model, mnist_train_loader, epochs=8, lr=0.003)
    base_sbohn = deepcopy(model)
    mnist_task = base_sbohn.save_task_params()
    base_sbohn_acc = evaluate(base_sbohn, mnist_test_loader)

    mlp = PermHeadMLP()
    train(mlp, mnist_train_loader, epochs=8, lr=0.003)
    base_mlp = deepcopy(mlp)
    base_mlp_acc = evaluate(base_mlp, mnist_test_loader)

    rows = {}
    saved_fashion_task = None
    saved_mlp_full = None
    for shots in (10, 50, 100, 500, 2000, 5000):
        adaptation_loader = loader(first_subset(fashion_train, shots), 128, True, SEED + shots)
        row = {}

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 8, 0.003, candidate.adaptation_params())
        row["perm_head"] = evaluate(candidate, fashion_test_loader)
        if shots == 5000:
            saved_fashion_task = candidate.save_task_params()

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 8, 0.003, candidate.head_only_params())
        row["head_only"] = evaluate(candidate, fashion_test_loader)

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 8, 0.003, candidate.perm_only_params())
        row["perm_only"] = evaluate(candidate, fashion_test_loader)

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 8, 0.003)
        row["full_tune"] = evaluate(candidate, fashion_test_loader)

        candidate_mlp = deepcopy(base_mlp)
        train(candidate_mlp, adaptation_loader, 8, 0.003, candidate_mlp.classifier.parameters())
        row["mlp_head"] = evaluate(candidate_mlp, fashion_test_loader)

        candidate_mlp = deepcopy(base_mlp)
        train(candidate_mlp, adaptation_loader, 8, 0.003)
        row["mlp_full"] = evaluate(candidate_mlp, fashion_test_loader)
        if shots == 5000:
            saved_mlp_full = candidate_mlp

        rows[str(shots)] = {key: round(value, 6) for key, value in row.items()}
        print(f"PERM_HEAD checkpoint shots={shots}/5000", flush=True)

    switch_model = deepcopy(base_sbohn)
    switch_model.load_task_params(saved_fashion_task)
    fashion_before = evaluate(switch_model, fashion_test_loader)
    switch_model.load_task_params(mnist_task)
    mnist_after = evaluate(switch_model, mnist_test_loader)
    switch_model.load_task_params(saved_fashion_task)
    fashion_after = evaluate(switch_model, fashion_test_loader)
    mlp_mnist_after = evaluate(saved_mlp_full, mnist_test_loader)

    return {
        "protocol": PROTOCOL,
        "shared_listing": 58,
        "reconstruction_choices": {
            "seed": SEED, "adaptation_epochs": 8, "adaptation_lr": 0.003,
            "test_samples": 1000,
            "note": "Fazy 2 i 3 nie występują w listingu; jawnie użyto parametrów fazy bazowej.",
        },
        "parameter_counts": {
            "model": parameter_count(base_sbohn),
            "perm_head": parameter_count_of(base_sbohn.adaptation_params()),
            "head_only": parameter_count_of(base_sbohn.head_only_params()),
            "perm_only": parameter_count_of(base_sbohn.perm_only_params()),
        },
        "base": {"sbohn_mnist": round(base_sbohn_acc, 6), "mlp_mnist": round(base_mlp_acc, 6)},
        "fewshot": rows,
        "continual": {
            "sbohn_mnist_before": round(base_sbohn_acc, 6),
            "sbohn_fashion": round(fashion_before, 6),
            "sbohn_mnist_after_restore": round(mnist_after, 6),
            "sbohn_fashion_after_restore": round(fashion_after, 6),
            "sbohn_mnist_degradation": round(base_sbohn_acc - mnist_after, 9),
            "mlp_mnist_before": round(base_mlp_acc, 6),
            "mlp_fashion": rows["5000"]["mlp_full"],
            "mlp_mnist_after_fashion": round(mlp_mnist_after, 6),
            "mlp_mnist_degradation": round(base_mlp_acc - mlp_mnist_after, 6),
        },
    }


def protocol_fewshot(data_root: Path) -> dict:
    """Uzupełnij komentarze PHASE 2/3 z listingu 59."""
    seed_all()
    mnist_train, mnist_test, fashion_train, fashion_test = load_datasets(data_root)
    mnist_train_loader = loader(balanced_subset(mnist_train, 3000), 64, True)
    mnist_test_loader = loader(mnist_test, 256, False)
    fashion_test_loader = loader(fashion_test, 256, False)

    sbohn = FewShotSBOHN()
    train(sbohn, mnist_train_loader, 5, 0.001)
    base_sbohn = deepcopy(sbohn)
    mnist_perms = base_sbohn.save_permutations()
    base_sbohn_acc = evaluate(base_sbohn, mnist_test_loader)

    mlp = SimpleMLP()
    train(mlp, mnist_train_loader, 5, 0.001)
    base_mlp = deepcopy(mlp)
    base_mlp_acc = evaluate(base_mlp, mnist_test_loader)

    cnn = SimpleCNN()
    train(cnn, mnist_train_loader, 5, 0.001)
    base_cnn = deepcopy(cnn)
    base_cnn_acc = evaluate(base_cnn, mnist_test_loader)

    rows = {}
    for shots in (10, 50, 100, 500):
        adaptation_loader = loader(balanced_subset(fashion_train, shots, SEED + shots), 64, True, SEED + shots)
        row = {}

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 5, 0.001, candidate.perm_only_params())
        row["sbohn_perm_only"] = evaluate(candidate, fashion_test_loader)

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 5, 0.001, candidate.head_only_params())
        row["sbohn_head_only"] = evaluate(candidate, fashion_test_loader)

        candidate = deepcopy(base_sbohn)
        train(candidate, adaptation_loader, 5, 0.001)
        row["sbohn_full_tune"] = evaluate(candidate, fashion_test_loader)

        candidate_mlp = deepcopy(base_mlp)
        train(candidate_mlp, adaptation_loader, 5, 0.001)
        row["mlp_fine_tune"] = evaluate(candidate_mlp, fashion_test_loader)

        candidate_cnn = deepcopy(base_cnn)
        train(candidate_cnn, adaptation_loader, 5, 0.001)
        row["cnn_fine_tune"] = evaluate(candidate_cnn, fashion_test_loader)

        scratch_mlp = SimpleMLP()
        train(scratch_mlp, adaptation_loader, 5, 0.001)
        row["mlp_scratch"] = evaluate(scratch_mlp, fashion_test_loader)

        rows[str(shots)] = {key: round(value, 6) for key, value in row.items()}
        print(f"FEWSHOT checkpoint shots={shots}/500", flush=True)

    continual_loader = loader(balanced_subset(fashion_train, 5000, SEED + 5000), 64, True, SEED + 5000)
    continual_sbohn = deepcopy(base_sbohn)
    train(continual_sbohn, continual_loader, 5, 0.001, continual_sbohn.perm_only_params())
    fashion_perm = evaluate(continual_sbohn, fashion_test_loader)
    continual_sbohn.load_permutations(mnist_perms)
    mnist_after_restore = evaluate(continual_sbohn, mnist_test_loader)

    continual_mlp = deepcopy(base_mlp)
    train(continual_mlp, continual_loader, 5, 0.001)
    fashion_mlp = evaluate(continual_mlp, fashion_test_loader)
    mnist_mlp_after = evaluate(continual_mlp, mnist_test_loader)

    return {
        "protocol": PROTOCOL,
        "shared_listing": 59,
        "reconstruction_choices": {
            "seed": SEED, "adaptation_epochs": 5, "adaptation_lr": 0.001,
            "note": "Fazy 2 i 3 są w listingu wyłącznie komentarzami; użyto tej samej liczby epok co w fazie bazowej.",
        },
        "parameter_counts": {
            "sbohn": parameter_count(base_sbohn),
            "perm_only": parameter_count_of(base_sbohn.perm_only_params()),
            "head_only": parameter_count_of(base_sbohn.head_only_params()),
            "mlp": parameter_count(base_mlp),
            "cnn": parameter_count(base_cnn),
        },
        "base": {
            "sbohn_mnist": round(base_sbohn_acc, 6),
            "mlp_mnist": round(base_mlp_acc, 6),
            "cnn_mnist": round(base_cnn_acc, 6),
        },
        "fewshot": rows,
        "continual": {
            "sbohn_mnist_before": round(base_sbohn_acc, 6),
            "sbohn_fashion_perm_only": round(fashion_perm, 6),
            "sbohn_mnist_after_restore": round(mnist_after_restore, 6),
            "sbohn_mnist_degradation": round(base_sbohn_acc - mnist_after_restore, 9),
            "mlp_mnist_before": round(base_mlp_acc, 6),
            "mlp_fashion": round(fashion_mlp, 6),
            "mlp_mnist_after_fashion": round(mnist_mlp_after, 6),
            "mlp_mnist_degradation": round(base_mlp_acc - mnist_mlp_after, 6),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, choices=("perm_head", "fewshot"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=ROOT / "reproduced" / "stage_11_dataset_cache")
    args = parser.parse_args()
    args.data_root.mkdir(parents=True, exist_ok=True)
    threads = max(1, min(4, os.cpu_count() or 1))
    torch.set_num_threads(threads)
    started = time.perf_counter()
    payload = protocol_perm_head(args.data_root) if args.protocol == "perm_head" else protocol_fewshot(args.data_root)
    payload["runtime"] = {
        "duration_seconds": round(time.perf_counter() - started, 6),
        "python": platform.python_version(), "torch": torch.__version__,
        "platform": platform.platform(), "threads": threads,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"RECONSTRUCTION PASS: {args.protocol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
