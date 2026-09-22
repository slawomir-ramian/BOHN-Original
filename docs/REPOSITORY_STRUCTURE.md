# Docelowa struktura repozytorium

```text
BOHN-Original/
├── README.md
├── docs/
│   ├── source/BOHN_PL.pdf
│   ├── EXPERIMENT_INDEX.md
│   ├── CANONICAL_SOURCE.md
│   └── REPRODUCTION_POLICY_PL.md
├── inventory/
│   ├── experiments.csv
│   └── appendix_listings.csv
├── bohn_core/
├── experiments/
│   ├── 02_bohn_foundation/
│   ├── 03_sbohn/
│   ├── 04_symmetry_discovery/
│   ├── 05_permutation_and_representation/
│   ├── 06_learnable_sbohn/
│   ├── 07_fractal_and_patch/
│   ├── 08_meta_sbohn/
│   ├── 09_adaptation_and_continual/
│   ├── 10_sota_and_scaling/
│   ├── 11_integrated_system/
│   ├── 12_moe_evolution/
│   ├── 13_rmig_fbohn/
│   └── 14_meta_fbohn/
├── tests/
├── tools/
└── pyproject.toml
```

Pierwszy pakiet wykonawczy `B-001`--`B-009` znajduje się w
`experiments/02_bohn_foundation/`. Wspólny adapter jest w
`src/bohn_original/foundation.py`, a runner w `tools/run_stage_03.py`.
Każde uruchomienie tworzy osobny katalog pod
`reproduced/stage_03_runs/`; wynikowy ZIP w `artifacts/` jest plikiem pochodnym
i nie jest śledzony przez Git.
