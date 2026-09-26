# Etap 09 — Fractal SBOHN i Permutation Transformer

## Zakres

Etap zachowuje pozycje 57–72 oryginalnej chronologii PDF-a:

`FR-001`, `FR-004`, `FR-002`, `FR-003`, `PT-001`, `PT-002`, `PT-003`,
`PT-004`, `PT-005`, `HR-001`, `HR-002`, `HR-003`, `HR-004`, `HR-005`,
`HR-006`, `HR-007`.

Kolejność nie jest sortowaniem numerów identyfikatorów. Jest dokładnym porządkiem
z audytowanego PDF-a, dlatego `FR-004` występuje przed `FR-002`.

## Granica opublikowanego kodu

- blok `verbatim` 13 zawiera pełny wspólny program `FR-002/FR-003`;
- blok `verbatim` 15 zawiera pełny program Patch SBOHN dla `PT-001`, `PT-002`,
  `PT-004` i `PT-005`;
- `PT-003` ma tabelę skalowania architektury, ale wspólny program nie wykonuje
  sweepu rozdzielczości;
- `FR-001`, `FR-004` oraz `HR-001`–`HR-007` mają wyniki tabelaryczne lub
  narracyjne, lecz brak kompletnego kodu wykonującego te konkretne testy.

Jednostki bez kodu docelowego pozostają `AUDITED_REPORTED_RESULT`. Jest to audyt
źródła, a nie negatywny wynik naukowy.

## Zasady wykonania

1. Historyczny kod jest zachowany bez zmian i kontrolowany skrótami SHA-256.
2. Wrapper kompatybilności przekierowuje historyczne ścieżki `/tmp` do repozytorium.
3. Transport danych może użyć zapasowego oficjalnego lustra tylko wtedy, gdy URL
   zapisany w monografii jest niedostępny; dane i algorytm pozostają niezmienione.
4. Każdy wspólny program jest wykonywany raz, a każda pozycja otrzymuje osobną
   klasyfikację wyniku.
5. `SMOKE` nie pobiera danych i nie zastępuje pełnego programu historycznego.
6. Różnica numeryczna jest wynikiem naukowym, nie błędem technicznym.
