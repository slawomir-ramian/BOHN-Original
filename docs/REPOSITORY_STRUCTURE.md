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
│   ├── 04_generalization_so2/
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

Rozdział SBOHN znajduje się w `experiments/03_sbohn/`. Jego jednostki są
uruchamiane według `inventory/source_chronology.csv`, ponieważ chronologia PDF-a
nie jest identyczna z numerycznym sortowaniem ID.

Adaptacyjny router i uogólnienie SO(2) znajdują się w
`experiments/04_generalization_so2/`. Kod wydrukowany w monografii pozostaje w
`historical/`, natomiast brakujące procedury wykonawcze są jawnie oddzielone w
`reconstruction/`.

Wykrywanie symetrii znajduje się w `experiments/04_symmetry_discovery/`.
Etap zachowuje pozycje 29--33 z PDF-a: `SD-001`--`SD-004`, a następnie
`ASD-001`. Kod historyczny jest uruchamiany bez modyfikacji, a lekkie sondy
smoke znajdują się poza katalogiem `historical/`.

Eksperymenty zaprojektowane po audycie, które nie są jednostkami źródłowego
PDF-a, mają osobny rejestr `inventory/supplementary_experiments.csv`. Dzięki
temu mogą potwierdzać mechanizmy publikacji bez zmiany kanonicznej liczby 115
jednostek ani ich kolejności. Pierwszym takim wpisem jest ASD-001R.
