# Etap 04 - analiza lokalnej reprodukcji SBOHN

## Środowisko autora i integralność

- Uruchomienie UTC: `2026-09-22T22:10:33+00:00`.
- System: Windows 10 x64.
- Python: 3.14.5.
- NumPy: 2.5.3.
- scikit-learn: 1.9.1.
- Procesory logiczne widoczne dla Pythona: 4.
- Testy kontraktowe: 6/6 `OK`.
- Jednostki wykonawcze: 11/11 `PASS`.
- Pliki `stderr`: 11/11 puste.
- Manifest SHA-256 archiwum wynikowego: `PASS` dla 24 plików.
- SHA-256 przesłanego ZIP-a:
  `1504c476013af66c173cce04417ef12549bd26900132806562d65fc382ad1e09`.

Pełny wynik lokalny znajduje się w
`reproduced/stage_04_runs/20260922T221033Z/`. Wyniki raportowane w monografii
pozostają osobno w katalogach `historical/` i nie zostały nadpisane.

## Ocena merytoryczna

**Główny wynik naukowy rozdziału SBOHN został potwierdzony bardzo mocno.**
Reprezentacja relacyjna oparta na symetrii Z3 daje dużą i stabilną przewagę,
pozostaje odporna na kontrolowane błędy symetrii oraz pozwala odróżnić
prawdziwą symetrię od losowych kandydatów. Wyniki negatywne `S-001`--`S-003`
także zachowano; pokazują one, że samo liniowe dublowanie cech nie wystarcza.

## Wynik jednostek w kolejności PDF-a

| Kolejność | ID | Reprodukcja | Ocena merytoryczna | Najważniejszy wynik |
|---:|---|---|---|---|
| 1 | S-001 | NONDETERMINISTIC | TEST NIESTABILNY, WNIOSEK ROZWOJOWY ZACHOWANY | Kod nie ustawia seedu NumPy. Lokalnie gain wyniósł -0,0093 zamiast +0,0020; pojedynczy bieg nie stanowi stabilnego benchmarku. |
| 2 | S-002 | REPORTED_SUPERSET_MATCH | WYNIK NEGATYWNY POTWIERDZONY | Wszystkie 7 linii drukowanych przez kod jest zgodnych; średni gain +0,0031, tylko 10/20 zwycięstw. Raport historyczny zawiera 3 dodatkowe statystyki. |
| 3 | S-003 | REPORTED_SUPERSET_MATCH | WYNIK NEGATYWNY POTWIERDZONY | Wszystkie 6 linii kodu jest zgodnych; gain -0,0040, 16/50 lepiej i 29/50 gorzej. Raport zawiera 2 dodatkowe statystyki. |
| 4 | S-004 | SOURCE_BUG_PRESERVED | EFEKT POTWIERDZONY | Accuracy 0,4970 -> 0,8725, gain +0,3755 i faktycznie 50/50 zwycięstw. Kod omyłkowo drukuje licznik `worse` z warunku `gains > 0`; błąd zachowano i ujawniono. |
| 5 | S-005 | CLOSE_MATCH | POTWIERDZONA | Najlepszy wariant `x_plus_abs_delta`: 0,8391 zamiast 0,8390; maksymalna różnica 0,0001. |
| 6 | S-006 | EXACT_MATCH | POTWIERDZONA | Pełne Z3: 0,5847 -> 0,8456, gain +0,2609; 50/50 zwycięstw. |
| 7 | S-010 | CONTRACT_MATCH | POTWIERDZONA | Referencyjny ekstraktor zachowuje porządek Z3 i mapuje wymiar 64 -> 192; odrzuca zły wymiar. |
| 8 | S-011 | EXACT_MATCH | POTWIERDZONA | Benchmark 100 seedów: 0,5871 +/- 0,0460 -> 0,8460 +/- 0,0236; gain +0,2589; 100/100 zwycięstw. |
| 9 | S-007 | EXACT_MATCH | POTWIERDZONA | `S3_A1_A2` osiąga 0,8471 i gain +0,2635; 100/100 zwycięstw. |
| 10 | S-008 | CLOSE_MATCH | POTWIERDZONA | Pełna krzywa odporności zachowana; jedyna różnica to 0,8040 zamiast 0,8039 dla `bad_20`. |
| 11 | S-009 | EXACT_MATCH | POTWIERDZONA | Prawdziwa symetria najlepsza w 30/30 prób; średnia ranga 1,00/51; przewaga nad najlepszym losowym kandydatem +0,1493. |

## Kluczowe porównania

| Metryka | Monografia | Reprodukcja | Różnica |
|---|---:|---:|---:|
| S-001 gain | +0,0020 | -0,0093 | -0,0113 |
| S-004 baseline | 0,4970 | 0,4970 | 0,0000 |
| S-004 cecha relacyjna | 0,8725 | 0,8725 | 0,0000 |
| S-005 `x_plus_abs_delta` | 0,8390 | 0,8391 | +0,0001 |
| S-006 `sigma3_plus_A1_A2` | 0,8456 | 0,8456 | 0,0000 |
| S-011 baseline LR | 0,5871 | 0,5871 | 0,0000 |
| S-011 SBOHN-LR | 0,8460 | 0,8460 | 0,0000 |
| S-011 gain | 0,2589 | 0,2589 | 0,0000 |
| S-008 `SBOHN_bad_20` | 0,8039 | 0,8040 | +0,0001 |
| S-009 prawdziwa symetria | 0,8471 | 0,8471 | 0,0000 |
| S-009 najlepszy losowy kandydat | 0,6979 | 0,6979 | 0,0000 |

## Wnioski

1. Najmocniejszy benchmark `S-011` odtworzył się dokładnie: przewaga SBOHN-LR
   wynosi 0,2589 i występuje dla wszystkich 100 seedów.
2. `S-009` potwierdza zdolność odkrywania symetrii, a nie tylko poprawę
   klasyfikacji: kandydat prawdziwy zajmuje pierwsze miejsce w każdym z 30
   przebiegów wobec 50 losowych kontroli.
3. `S-008` zachowuje uporządkowaną degradację jakości przy pogarszaniu
   symetrii. Różnica 0,0001 nie ma znaczenia merytorycznego.
4. `S-002` i `S-003` potwierdzają ważny wynik negatywny: proste dublowanie
   liniowe nie daje stabilnej przewagi. Przełom następuje po wprowadzeniu
   nieliniowej obserwabli relacyjnej `|x-g(x)|` w `S-004`.
5. `S-001` nie jest reprodukowalnym benchmarkiem liczbowym, ponieważ historyczny
   listing nie ustawia seedu danych. Rozbieżność pojedynczego biegu jest cechą
   źródła, nie dowodem przeciw SBOHN.
6. Błąd licznika `worse` w `S-004` dotyczy wyłącznie jednej linii wydruku.
   Obliczone accuracy i gain są zgodne z monografią, więc wniosek naukowy
   pozostaje nienaruszony.
7. Chronologia źródłowa została zachowana:
   `S-001, S-002, S-003, S-004, S-005, S-006, S-010, S-011, S-007, S-008, S-009`.

## Decyzja archiwalna

Nie poprawiamy historycznych listingów ani wydruków. Zachowujemy równolegle:

- `RESULT_REPORTED` - treść monografii,
- `RESULT_REPRODUCED` - wynik współczesnego wykonania,
- jawny status zgodności i interpretację rozbieżności,
- oryginalną kolejność PDF-a niezależnie od numeracji ID.
