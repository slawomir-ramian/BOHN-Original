# Etap 04 - rekonstrukcja SBOHN

Zakres obejmuje 11 jednostek rozdziału 3 monografii. Wyodrębniono 11 listingów
wykonawczych, 9 wyników zapisanych jako kolejne bloki `lstlisting` oraz wynik
`S-011` zapisany w bloku `verbatim`. `S-010` jest referencyjną implementacją
klas bez osobnego przebiegu wynikowego.

## Zasady

- kod historyczny pozostaje bajtowo zgodny ze źródłem,
- pełny runner wykonuje kod historyczny bez przepisywania algorytmów,
- surowe `stdout` i `stderr` są zachowywane dla każdej jednostki,
- ZIP pełnego przebiegu zawiera raport, JSON, surowe wydruki i manifest SHA-256,
- różnica tekstowa lub liczbowa nie jest automatycznie oceną merytoryczną.

## Ujawnione cechy źródła

1. `S-001` nie ustawia seedu globalnego NumPy, więc nie jest deterministyczny.
2. Wyniki `S-002` i `S-003` zawierają dodatkowe statystyki niewypisywane przez
   odpowiadający im kod.
3. W `S-004` linia opisana jako liczba przypadków „worse” ponownie używa warunku
   `gains > 0`. Historyczny błąd zostaje zachowany, a raport go opisuje.
4. `S-009` wykonuje 30 przebiegów po 50 losowych permutacji, czyli 1500 modeli
   kontrolnych; dlatego jest najcięższą jednostką etapu.

## Zamknięcie

Pełny przebieg autora z `2026-09-22T22:10:33Z` zakończył się powodzeniem dla
wszystkich 11 jednostek. Ostateczna analiza zgodności liczbowej i wartości
merytorycznej znajduje się w `docs/STAGE_04_LOCAL_ANALYSIS.md`.
