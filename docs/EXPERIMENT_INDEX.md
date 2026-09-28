# Indeks eksperymentów, testów i programów

Rejestr obejmuje **115 jednostek** wykrytych w monografii.
Po zakończonych etapach wykonano **108 jednostek**; **7** pozostaje `NOT_RUN`.

Kolumna `Kod` opisuje poziom materiału dostępnego w PDF. `NARRATIVE_ONLY` nie
oznacza pominięcia - przeciwnie, wskazuje jednostkę wymagającą ostrożnej rekonstrukcji
z opisu i tabel, bez udawania, że pełny kod został opublikowany.

## Rozdział 2: BOHN - fundament orbitowy

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `B-001` | 2.1.4 | Wyznaczanie orbit grupy Z3 na 64 stanach | program_test | 15 / 16 | `FULL` | `EXACT_MATCH` |
| `B-002` | 2.2.1 | Obliczanie histogramu orbitowego Phi(X) | program_test | 16 / 17 | `FULL` | `EXACT_MATCH` |
| `B-003` | 2.3.1 | ReversibleRMIGLayer - forward i inverse | program | 16 / 17 | `FULL` | `EXACT_MATCH` |
| `B-004` | 2.4.1 | Testy odwracalności i poprawności gradientów | test | 16-17 / 17-18 | `FULL` | `CLOSE_MATCH` |
| `B-005` | 2.5 | Benchmark I - problem liniowy | benchmark | 17 / 18 | `FULL` | `DIVERGENT` |
| `B-006` | 2.6 | Benchmark II - problem Z3-symetryczny z etykietą kwadratową | benchmark | 17-18 / 18-19 | `FULL` | `PARTIAL` |
| `B-007` | 2.7 | Benchmark III - Orbit Energy Network | benchmark | 18 / 19 | `FULL` | `DIVERGENT` |
| `B-008` | 2.8 | Benchmark IV - Orbit Histogram Network (BOHN) | benchmark | 18-19 / 19-20 | `FULL` | `DIVERGENT` |
| `B-009` | 2.9 | Test inwariantności histogramu orbitowego względem Z3 | test | 19 / 20 | `FULL` | `CLOSE_MATCH` |

## Rozdział 3: SBOHN - złamanie symetrii

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `S-001` | 3.2.1 | SBOHN-1 - dublet z MLP | experiment_negative | 24 / 25 | `FULL` | `NONDETERMINISTIC` |
| `S-002` | 3.2.2 | SBOHN-2 - dublet przy małej liczbie danych | experiment_negative | 24 / 25 | `FULL` | `REPORTED_SUPERSET_MATCH` |
| `S-003` | 3.2.3 | SBOHN-3 - test liniowy x vs [x+g(x), x-g(x)] | experiment_negative | 24 / 25 | `FULL` | `REPORTED_SUPERSET_MATCH` |
| `S-004` | 3.3.1 | SBOHN-4 - czysty test \|x-g(x)\| | experiment | 24 / 25 | `FULL` | `SOURCE_BUG_PRESERVED` |
| `S-005` | 3.3.2 | SBOHN-5 - porównanie wariantów cech | experiment | 24-25 / 25-26 | `FULL` | `CLOSE_MATCH` |
| `S-006` | 3.4.1 | SBOHN-6 - rozszerzenie na pełną grupę Z3 | experiment | 25-27 / 26-28 | `FULL` | `EXACT_MATCH` |
| `S-010` | 3.4.3 | SBOHN-LR - referencyjny model i kod implementacji | program | 25-27 / 26-28 | `FULL_UNCAPTIONED` | `CONTRACT_MATCH` |
| `S-011` | 3.4.3 | SBOHN-LR - referencyjny benchmark 100 seedów | benchmark | 25-27 / 26-28 | `FULL_UNCAPTIONED` | `EXACT_MATCH` |
| `S-007` | 3.5.1 | SBOHN-7 - losowe współrzędne i wagi | stability_test | 27 / 28 | `FULL` | `EXACT_MATCH` |
| `S-008` | 3.5.2 | SBOHN-8 - odporność na błędną symetrię | robustness_test | 27 / 28 | `FULL` | `CLOSE_MATCH` |
| `S-009` | 3.6.1 | SBOHN-9 - ranking kandydatów i wykrywanie ukrytej symetrii | discovery_test | 27-28 / 28-29 | `FULL` | `EXACT_MATCH` |

## Rozdział 4: Uogólnienia i odkrywanie symetrii

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `G-001` | 4.1 | Adaptacyjny Router Permutacji z kryterium Fishera na Iris | experiment | 29-31 / 30-32 | `FULL` | `EXACT_MATCH` |
| `SO-001` | 4.2.1 | SO(2) - numeryczna weryfikacja zerowania symetryzatora | numerical_test | 31 / 32 | `FULL` | `CLOSE_MATCH` |
| `SO-002` | 4.2.2 | SO(2) - profil asymetrii numeryczny vs analityczny | numerical_test | 31-32 / 32-33 | `PARTIAL` | `FORMULA_MATCH` |
| `SO-003` | 4.2.3 | SO(2) - momenty M1-M6 numeryczne vs analityczne | numerical_test | 31-32 / 32-33 | `PARTIAL` | `FORMULA_MATCH` |
| `SO-004` | 4.2.4 | SO(2) - współczynniki Fouriera rozróżniają orientację | numerical_test | 32 / 33 | `PARTIAL` | `FORMULA_MATCH` |
| `SO-005` | 4.2.6 | SO(2)-SBOHN - klasyfikacja w R4 | experiment | 32-33 / 33-34 | `FULL` | `PARTIAL_RECONSTRUCTION` |
| `SO-006` | 4.2.6 | SO(2)-SBOHN - klasyfikacja w R8 | experiment | 32-33 / 33-34 | `FULL` | `PARTIAL_RECONSTRUCTION` |
| `SO-007` | 4.2.6 | SO(2)-SBOHN - test inwariantności reprezentacji | test | 32-33 / 33-34 | `PARTIAL` | `CLOSE_MATCH` |
| `SD-001` | 4.3.2 | Symmetry Discovery 1 - symetria przesunięcia na digits | discovery_test | 34-35 / 35-36 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `SD-002` | 4.3.3 | Symmetry Discovery 2 - kontrola negatywna z losowymi etykietami | negative_control | 35-36 / 36-37 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `SD-003` | 4.3.4 | Symmetry Discovery 3 - ukryta symetria odbicia poziomego | discovery_test | 36-38 / 37-39 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `SD-004` | 4.3.5 | Symmetry Discovery 4 - ukryta symetria obrotu o 180 stopni | discovery_test | 38-39 / 39-40 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `ASD-001` | 4.4 | Autonomous Symmetry Discovery - selekcja kandydatów | discovery_test | 40-41 / 41-42 | `FULL_UNCAPTIONED` | `PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH` |

## Rozdział 5: Uczenie permutacji i autonomiczna reprezentacja

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `PL-001` | 5.1 | SBOHN-PL - ewolucyjne uczenie permutacji rotate180 | experiment | 43-47 / 44-48 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `PL-002` | 5.2.1 | SBOHN-PL2 - uczenie dwóch permutacji jednocześnie | experiment | 47-48 / 48-49 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `PL-003` | 5.2.2 | SBOHN-K - skalowanie liczby permutacji | scaling_test | 48-49 / 49-50 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `AR-001` | 5.3.2 | SBOHN-AR v1 - ewolucyjne generowanie jednej transformacji | experiment | 49-50 / 50-51 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `AR-002` | 5.3.3 | SBOHN-AR v2 - Generate-Represent-Select | experiment | 50-52 / 51-53 | `FULL_UNCAPTIONED` | `CONCLUSION_MATCH` |
| `AR-003` | 5.4.1 | SBOHN-AR - test korelacji reprezentacji | analysis_test | 52-53 / 53-54 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `AR-004` | 5.4.2 | SBOHN-AR - reprezentacyjne klasy równoważności | analysis_test | 53-55 / 54-56 | `FULL_UNCAPTIONED` | `CLOSE_NUMERIC_MATCH` |
| `HD-001` | 5.5.5 | SBOHN - skalowanie względem wymiaru d=63..4095 | scaling_test | 56 / 57 | `FULL_UNCAPTIONED` | `CONCLUSION_MATCH` |
| `HD-002` | 5.5.7 | SBOHN - wpływ liczby próbek przy d=4095 | scaling_test | 57 / 58 | `FULL_UNCAPTIONED` | `CONCLUSION_MATCH` |
| `HD-003` | 5.5.11 | SBOHN - wariant proportional-signal | robustness_test | 57-58 / 58-59 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `CMP-001` | 5.6.2 | SBOHN-AE - PCA-48 vs autoenkoder rekonstrukcyjny | compression_test | 58-59 / 59-60 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `CMP-002` | 5.6.3 | SBOHN-SRL - supervised latent k=2,4,8,16 vs PCA | compression_test | 59-60 / 60-61 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |

## Rozdział 6: Learnable SBOHN i Log-Domain Sinkhorn

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `LS-001` | 6.2.2-6.2.3 | Learnable SBOHN - pięciokrokowy pipeline Task A i Task B | experiment_suite | 64-65 / 65-66 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `LS-002` | 6.2.4 EXP 1 | SBOHN-K3 - regularyzacja ortogonalności | ablation | 65 / 66 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `LS-003` | 6.2.4 EXP 2 | Input-Dependent SBOHN - wyżarzanie temperatury i eksplozja NaN | stability_test_negative | 65-66 / 66-67 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `LS-004` | 6.2.4 EXP 3 | Low-Rank Sinkhorn 784x784 - sweep rangu | scaling_ablation | 66 / 67 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `LS-005` | 6.2.4 EXP 4 | Analiza algebraiczna wyuczonych macierzy i podgrup | analysis_test_negative | 66 / 67 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `LS-006` | 6.2.4 EXP 5 | Task C - regresja z czterema ukrytymi symetriami | experiment | 66-67 / 67-68 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `LD-001` | 6.3.1 | Log-domain vs naive Sinkhorn | stability_test | 67-68 / 68-69 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `LD-002` | 6.3.2 | Input-Dependent log-domain z wyżarzaniem temperatury | stability_test | 68 / 69 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `LD-003` | 6.3.3 | Regularyzacja entropii - Global K=3 | ablation | 68 / 69 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `LD-004` | 6.3.4 | Full Stack - InpDep K=2 + LogDomain + Entropy + Ortho | experiment | 68-69 / 69-70 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `LD-005` | 6.3.5 | Analiza algebraiczna modelu z regularyzacją entropii | analysis_test | 69 / 70 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |

## Rozdział 7: Architektura fraktalna i Permutation Transformer

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `FR-001` | 7.1 | Fractal Input-Dependent SBOHN - test przełomowy i analiza per-level | experiment | 71-73 / 72-74 | `CHAPTER_NARRATIVE_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `FR-004` | 7.1.4 | Fractal SBOHN - osobna analiza per-level modelu InpDep 5L | analysis_test | 72-73 / 73-74 | `CHAPTER_NARRATIVE_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `FR-002` | 7.2 | Fractal SBOHN - MNIST | experiment | 75-81 / 76-82 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `FR-003` | 7.2 | Fractal SBOHN - Fashion-MNIST | experiment | 75-81 / 76-82 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `PT-001` | 7.3 | Patch SBOHN / Permutation Transformer - MNIST | experiment | 83-89 / 84-90 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `PT-002` | 7.3 | Patch SBOHN / Permutation Transformer - Fashion-MNIST | experiment | 83-89 / 84-90 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `PT-003` | 7.3.1 | Patch SBOHN - skalowanie względem rozdzielczości | scaling_test | 83-84 / 84-85 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `PT-004` | 7.3.2-7.3.3 | Patch SBOHN - ablation input-dependency | ablation | 84 / 85 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `PT-005` | 7.3.2-7.3.3 | Patch SBOHN - ablation liczby głów | ablation | 84 / 85 | `FULL_IN_CHAPTER` | `CLOSE_NUMERIC_MATCH` |
| `HR-001` | 7.4 | HighRes Patch SBOHN - test 4K na MNIST | scaling_test | 90-91 / 91-92 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-002` | 7.4 | HighRes Patch SBOHN - test 4K na Fashion-MNIST | scaling_test | 90-91 / 91-92 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-003` | 7.5 | HighRes Fractal SBOHN v2 - permutacja patchy vs cech | experiment | 92-93 / 93-94 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-004` | 7.4.3 | HighRes Patch SBOHN - pełne skalowanie rozdzielczości do 4K | scaling_test | 91-92 / 92-93 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-005` | 7.5.2 | HighRes Fractal SBOHN v2 - wkład poszczególnych poprawek | ablation | 93 / 94 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-006` | 7.5.2 | HighRes Fractal SBOHN v2 - MNIST | experiment | 93 / 94 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `HR-007` | 7.5.2 | HighRes Fractal SBOHN v2 - Fashion-MNIST | experiment | 94 / 95 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |

## Rozdział 8: Meta-SBOHN

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `MS-001` | 8.1.1 | Meta-SBOHN Score Generator v1 | experiment | 95-96 / 96-97 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-002` | 8.1.2 | Meta-SBOHN v2 - Geometry-Aware Generator | experiment | 96 / 97 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-003` | 8.1.3 | Meta-SBOHN v2 + SRL | experiment | 96 / 97 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-004` | 8.1.4 | Meta-Meta-SBOHN v1 | experiment | 96-97 / 97-98 | `NARRATIVE_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-005` | 8.1.5 | SBOHN-Curriculum v1 - prosty warm-start | experiment | 97 / 98 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-006` | 8.1.6 | SBOHN-Curriculum v2 - Mixed Population Transfer | experiment | 97-98 / 98-99 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-007` | 8.1.7 | SBOHN-Curriculum v3 - transfer elit | experiment | 98 / 99 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-008` | 8.1.7 | SBOHN-Curriculum v4 - analiza basinów | analysis_test | 98 / 99 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MS-009` | 8.1.8 | Meta-SBOHN v5 - Geometry Regularization | ablation | 98 / 99 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |
| `MS-010` | 8.1.9 | Meta-SBOHN v6 - Geometry Annealing | ablation | 98-99 / 99-100 | `FULL_SHARED_LISTING` | `CLOSE_NUMERIC_MATCH` |

## Rozdział 9: Adaptacja zadaniowa i continual learning

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `AD-001` | 9.1 | Perm+Head - porównanie sześciu metod adaptacji | experiment_suite | 100-102 / 101-103 | `SOURCE_FRAGMENT_ONLY` | `NUMERIC_DIFFERENCE` |
| `AD-002` | 9.2.1-9.2.2 | Few-shot transfer MNIST -> Fashion-MNIST | transfer_test | 102-103 / 103-104 | `SOURCE_FRAGMENT_ONLY` | `CONCLUSION_MATCH` |
| `AD-003` | 9.2.4 | Head-only vs full-tune - test modularności enkodera | ablation | 103 / 104 | `SOURCE_FRAGMENT_ONLY` | `CONCLUSION_MATCH` |
| `CL-001` | 9.3 | Continual learning - przełączanie zadań i forgetting | continual_test | 103-104 / 104-105 | `SOURCE_FRAGMENT_ONLY` | `CLOSE_NUMERIC_MATCH` |
| `CL-002` | 9.3.1 | Continual learning - wariant perm-only z większym modelem | continual_test | 104 / 105 | `SOURCE_FRAGMENT_ONLY` | `CONCLUSION_MATCH` |

## Rozdział 10: Porównanie SOTA i skalowanie

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `SOTA-001` | 10.1-10.2 | Porównanie accuracy modeli na Fashion-MNIST | benchmark | 106-107 / 107-108 | `FULL` | `CONCLUSION_MATCH` |
| `SOTA-002` | 10.3 | Benchmark skalowania inferencji z rozdzielczością do 4K | scaling_benchmark | 107-109 / 108-110 | `FULL` | `CONCLUSION_MATCH` |

## Rozdział 11: Kierunki badawcze i system zintegrowany

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `SYS-001` | 11.1 | Meta-learned Permutation Generator | experiment | 111-112 / 112-113 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `SYS-002` | 11.2 | Multi-task MoE Routing | experiment | 112-113 / 113-114 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `SYS-003` | 11.3.1 | Deep Encoder - skalowanie głębokości | scaling_test | 113 / 114 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `SYS-004` | 11.3.2 | Partial Unfreeze - odmrażanie wybranych warstw | ablation | 113-114 / 114-115 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `SYS-005` | 11.4 | System zintegrowany MoE + Meta-Generator + Frozen Encoder | experiment | 114-116 / 115-117 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `CPU-001` | 11.5.1 | Bateria CPU 1 - Shallow vs Deep Encoder | experiment | 116 / 117 | `FULL_SHARED_LISTING` | `NUMERIC_DIFFERENCE` |
| `CPU-002` | 11.5.2 | Bateria CPU 2 - MoE Multi-Domain Routing | experiment | 116-117 / 117-118 | `FULL_SHARED_LISTING` | `CONCLUSION_MATCH` |
| `CPU-003` | 11.5.3 | Bateria CPU 3 - Cross-Domain Meta-Generator | experiment | 116-117 / 117-118 | `FULL_SHARED_LISTING` | `NUMERIC_DIFFERENCE` |
| `CPU-004` | 11.5.4 | Bateria CPU 4 - Partial Unfreeze: accuracy vs forgetting | experiment | 117 / 118 | `FULL_SHARED_LISTING` | `CONCLUSION_MATCH` |
| `CPU-005` | 11.5.5 | Bateria CPU 5 - Few-Shot Scaling z frozen encoder | scaling_test | 117-118 / 118-119 | `FULL_SHARED_LISTING` | `CONCLUSION_MATCH` |

## Rozdział 12: Ewolucja MoE

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `MOE-001` | 12.1 | Partial Unfreeze + MoE - eliminacja zapominania | experiment | 119-121 / 120-122 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MOE-009` | 12.1.3 | Partial Unfreeze + MoE - osobny test trzech domen | experiment | 120-121 / 121-122 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MOE-002` | 12.2.2 | Sparse MoE + Gate Specialization Loss - expert collapse | experiment_negative | 121-122 / 122-123 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MOE-003` | 12.2.3 | Sparse MoE - sweep lambda_spec | ablation_negative | 121-122 / 122-123 | `SOURCE_FRAGMENT_ONLY` | `AUDITED_REPORTED_RESULT` |
| `MOE-004` | 12.3 | Hard Assignment + Gate Distillation | experiment | 122-123 / 123-124 | `FULL` | `NUMERIC_DIFFERENCE` |
| `MOE-005` | 12.4.1-12.4.3 | LayerNorm vs BatchNorm - routing experiments | ablation | 123-124 / 124-125 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `MOE-006` | 12.4.4 | Confidence routing | experiment | 124 / 125 | `FULL_SHARED_LISTING` | `CONCLUSION_MATCH` |
| `MOE-007` | 12.4.5 | Shared Expert - wynik negatywny | experiment_negative | 124 / 125 | `SHARED_LISTING_TARGET_CODE_ABSENT` | `AUDITED_REPORTED_RESULT` |
| `MOE-008` | 12.5 | Hybrid BN/LN - kulminacja | experiment | 125-127 / 126-128 | `FULL` | `NUMERIC_DIFFERENCE` |

## Rozdział 13: RMIG-FBOHN

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `RF-001` | 13.4 | RMIG-FBOHN v1 | experiment | 129 / 130 | `FULL_SUITE` | `NOT_RUN` |
| `RF-002` | 13.5 | RMIG-FBOHN - test out-of-representation | robustness_test | 129-130 / 130-131 | `FULL_SUITE` | `NOT_RUN` |

## Rozdział 14: Meta-FBOHN

| ID | Sekcja | Jednostka | Typ | Strony drukowane / PDF | Kod | Reprodukcja |
|---|---|---|---|---|---|---|
| `MF-001` | 14.2 | Meta-FBOHN v1 - negatywny wynik skalowania cech | experiment_negative | 131 / 132 | `FULL_SUITE` | `NOT_RUN` |
| `MF-002` | 14.2 | Meta-FBOHN v2 - negatywny wynik skalowania cech | experiment_negative | 131-132 / 132-133 | `FULL_SUITE` | `NOT_RUN` |
| `MF-003` | 14.3 | Meta-FBOHN v3 - Learned Orbit Mixing | experiment | 132 / 133 | `FULL_SUITE` | `NOT_RUN` |
| `MF-004` | 14.4 | Meta-FBOHN v4 - Symbolic Orbit Composer | experiment | 132-133 / 133-134 | `FULL_SUITE` | `NOT_RUN` |
| `MF-005` | 14.5 | Meta-FBOHN v5 - Symbolic Library Discovery | experiment | 133-134 / 134-135 | `FULL_SUITE` | `NOT_RUN` |

