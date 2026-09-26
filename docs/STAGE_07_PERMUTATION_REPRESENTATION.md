# Etap 07 — uczenie permutacji i autonomiczna reprezentacja

## Zakres

Etap zachowuje pozycje 34--45 audytowanej chronologii PDF-a:

1. `PL-001` — SBOHN-PL, ewolucyjne uczenie jednej permutacji.
2. `PL-002` — SBOHN-PL2, dwie permutacje.
3. `PL-003` — SBOHN-K, skalowanie liczby permutacji.
4. `AR-001` — autonomiczne generowanie transformacji, wariant v1.
5. `AR-002` — Generate--Represent--Select, wariant v2.
6. `AR-003` — korelacja reprezentacji.
7. `AR-004` — reprezentacyjne klasy równoważności.
8. `HD-001` — skalowanie wymiaru.
9. `HD-002` — wpływ liczby próbek dla `d=4095`.
10. `HD-003` — wariant proportional-signal.
11. `CMP-001` — PCA-48 kontra autoenkoder rekonstrukcyjny.
12. `CMP-002` — nadzorowany latent `k=2,4,8,16`.

## Granica dowodowa

Pełny kod opublikowano dla siedmiu jednostek: `PL-001`, `AR-001`--`AR-004`,
`HD-001` i `HD-002`. Dla pięciu pozostałych publikacja zawiera opis i wyniki,
ale nie pełny program. Są one zachowane jako `NARRATIVE_ONLY` i walidowane
w trybie `AUDITED_REPORTED_RESULT`. Ten status nie jest błędem wykonania ani
rekonstrukcją wyniku.

Listing wysokowymiarowy jest w publikacji rozdzielony na funkcję cech i program
główny. Oba fragmenty są zachowane oddzielnie i uruchamiane przez bezstronne
złożenie w pamięci; żaden fragment historyczny nie jest modyfikowany.

## Kryteria interpretacyjne

Porównanie numeryczne jest pomocnicze, ponieważ wersje `numpy`, `pandas` i
`scikit-learn` mogą zmieniać szczegóły optymalizacji. Kluczowe wnioski są
kontrolowane osobno: przewaga ewolucji nad baseline/random, przewaga SBOHN w
każdym wymiarze oraz wysoka CKA przy niskiej zgodności permutacji.
