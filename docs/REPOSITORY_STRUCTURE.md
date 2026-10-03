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
│   ├── 06_learnable_sinkhorn/
│   ├── 07_fractal_patch/
│   ├── 08_meta_sbohn/
│   ├── 09_adaptation_and_continual/
│   ├── 10_sota_and_scaling/
│   ├── 11_integrated_system/
│   ├── 12_moe_evolution/
│   └── 13_rmig_meta_fbohn/
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

Uczenie permutacji, autonomiczna reprezentacja, skalowanie wysokowymiarowe
i kompresja z rozdziału 5 znajdują się w
`experiments/05_permutation_and_representation/`. Jednostki z kodem zachowują
niezmienione listingi w `historical/`; jednostki `NARRATIVE_ONLY` przechowują
dokładny fragment wyniku źródłowego, bez fikcyjnego kodu historycznego.

Pięć jawnych rekonstrukcji rozdziału 5 znajduje się osobno w
`experiments/05_permutation_and_representation_supplementary/`. Mają sufiks
`R`, zamrożony protokół `STAGE_07R_V1` i pozostają poza chronologią PDF-a.
Pełny wynik ma status częściowy: cztery z pięciu kryteriów potwierdzono.

Learnable SBOHN i Log-Domain Sinkhorn z rozdziału 6 znajdują się w
`experiments/06_learnable_sinkhorn/`. Listing 53 jest zachowany jako wspólny
kontekst `LS-001`--`LS-006`, ale tylko `LS-001` ma w nim kod docelowego
eksperymentu. Listingi 54 i 55 są wykonywane jednokrotnie, a wyniki są
klasyfikowane osobno dla `LD-001`--`LD-005`.

Fractal SBOHN, Patch SBOHN i jednostki HighRes z rozdziału 7 znajdują się w
`experiments/07_fractal_patch/`. Dwa kompletne programy historyczne są
uruchamiane po jednym razie, a sześć zależnych jednostek otrzymuje osobne
porównania. Pozycje bez kompletnego kodu docelowego przechowują dokładne
wyniki publikacji i pozostają jawnie oznaczone jako audytowe.

Meta-SBOHN z rozdziału 8 znajduje się w `experiments/08_meta_sbohn/`.
Jednostki `MS-009` i `MS-010` dzielą pełny historyczny program 20-seedowy.
Jednostki curriculum zachowują niezmieniony fragment inicjalizacji populacji,
ale nie są przedstawiane jako wykonywalne bez brakującej reszty protokołu.

Adaptacja zadaniowa i continual learning z rozdziału 9 znajdują się w
`experiments/09_adaptation_and_continual/`. Niezmienione fragmenty listingów
58 i 59 są w `historical/`, a uzupełnione fazy eksperymentalne są jawnie
oddzielone w `reconstruction/`. Dwa wspólne przebiegi z checkpointami obsługują
pięć jednostek w kolejności PDF-a.

Porównanie SOTA i benchmark skalowania z rozdziału 10 znajdują się w
`experiments/10_sota_and_scaling/`. Pełne listingi 60 i 61 są przechowywane
w `historical/`. Wykonanie odbywa się przez tymczasową kopię zgodności, która
zmienia jedynie absolutne ścieżki `/tmp`; pliki historyczne pozostają
niezmienione i są kontrolowane sumami SHA-256.

Cztery kierunki badawcze, system zintegrowany i bateria CPU z rozdziału 11
znajdują się w `experiments/11_integrated_system/`. Pozycje `SYS` zachowują
fragmenty definicji architektur bez udawania, że publikują brakujące pętle
treningu. Pozycje `CPU` współdzielą pełny listing 64 i jeden checkpoint biegu.
Wynik pełnego biegu oraz uczciwa klasyfikacja dwóch rozbieżności znajdują się w
`reproduced/stage_13_runs/20260928T051822Z/` i
`docs/STAGE_13_LOCAL_ANALYSIS.md`.

Ewolucja MoE z rozdziału 12 znajduje się w
`experiments/12_moe_evolution/`. Trzy pełne programy historyczne wykonują
Hard Assignment, Confidence Routing i Hybrid BN/LN. Pozostałe sześć pozycji
przechowuje dokładny kontekst źródłowy i tabele, lecz pozostaje audytem z
powodu braku opublikowanej pętli docelowej. Pełny bieg znajduje się w
`reproduced/stage_14_runs/20260928T180446Z/`, a interpretacja rozbieżności w
`docs/STAGE_14_LOCAL_ANALYSIS.md`.

RMIG-FBOHN i Meta-FBOHN z rozdziałów 13–14 znajdują się wspólnie w
`experiments/13_rmig_meta_fbohn/`, zgodnie z tym, że wszystkie siedem pozycji
dzieli kompletny listing 71. Checkpointy pełnego protokołu są oddzielone od
niezmienionych źródeł historycznych. Pełny bieg znajduje się w
`reproduced/stage_15_runs/20260928T185044Z/`, a szczegółowa interpretacja w
`docs/STAGE_15_LOCAL_ANALYSIS.md`. Tym etapem zakończono wszystkie 115 pozycji.

<!-- STAGE_16_SUPPLEMENTARY_START -->
## Rozszerzenie po wydaniu v1.0.0: Etap 16

- `experiments/14_sota002_high_resolution_supplementary/` — protokół i dwie jednostki;
- `src/bohn_original/stage16_high_resolution.py` — nowy wariant H;
- `reproduced/stage_16_runs/` — wyniki i manifesty;
- `docs/STAGE_16_LOCAL_ANALYSIS.md` — kontrolowana interpretacja.
<!-- STAGE_16_SUPPLEMENTARY_END -->
