# Etap 02 - audyt krzyżowy monografii

## Wynik

Indeks wzrósł ze 103 do **115 jednostek**. Dodano 12 pozycji, które w
pierwszym rejestrze były ukryte wewnątrz szerszych eksperymentów.

| Nowe ID | Powód wydzielenia |
|---|---|
| `S-010` | SBOHN-LR - referencyjny model i kod implementacji |
| `S-011` | SBOHN-LR - referencyjny benchmark 100 seedów |
| `FR-004` | Fractal SBOHN - osobna analiza per-level modelu InpDep 5L |
| `PT-003` | Patch SBOHN - skalowanie względem rozdzielczości |
| `PT-004` | Patch SBOHN - ablation input-dependency |
| `PT-005` | Patch SBOHN - ablation liczby głów |
| `HR-004` | HighRes Patch SBOHN - pełne skalowanie rozdzielczości do 4K |
| `HR-005` | HighRes Fractal SBOHN v2 - wkład poszczególnych poprawek |
| `HR-006` | HighRes Fractal SBOHN v2 - MNIST |
| `HR-007` | HighRes Fractal SBOHN v2 - Fashion-MNIST |
| `CL-002` | Continual learning - wariant perm-only z większym modelem |
| `MOE-009` | Partial Unfreeze + MoE - osobny test trzech domen |

## Warstwy kontroli

1. **115 jednostek** w `inventory/experiments.csv`.
2. **94 numerowane tabele** w `inventory/table_map.csv`.
3. **44 podpisane listingi** A.1-A.43 i B.1 w `inventory/appendix_listings.csv`.
4. **24 bloki bez osobnego podpisu lub skrypty wieloeksperymentalne**
   w `inventory/code_block_map.csv`.
5. **74 bloków `lstlisting`** i **20 bloków `verbatim`**
   z dokładnymi numerami linii oraz hashami SHA-256.
6. Osobne oznaczenie pozycji z pełnym kodem, kodem częściowym i opisem narracyjnym.

## Granica audytu

Audyt potwierdza kompletność rejestru na poziomie rozpoznawalnych jednostek
wykonawczych w PDF. Nie potwierdza jeszcze, że każdy listing jest wykonywalny bez
rekonstrukcji: tę właściwość sprawdzimy osobno podczas ekstrakcji kodu B-001, B-002, ...
