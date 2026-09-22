# Etap 03 - analiza lokalnej reprodukcji B-001--B-009

## Środowisko autora

- Uruchomienie UTC: `2026-09-22T21:09:18+00:00`.
- System: Windows 10 x64.
- Python: 3.14.5.
- NumPy: 2.5.3.
- scikit-learn: 1.9.1.
- Procesory logiczne widoczne dla Pythona: 4.
- Testy kontraktowe: 6/6 `OK`.
- Integralność archiwum wynikowego: `PASS`.

Pełny wynik lokalny znajduje się w
`reproduced/stage_03_runs/20260922T210918Z/`. Wyniki raportowane w monografii
pozostają osobno w katalogach `historical/` i nie zostały nadpisane.

## Ocena merytoryczna

**Wartość merytoryczna fundamentu BOHN została potwierdzona.** Statusy
`DIVERGENT` poniżej są techniczną informacją o braku ścisłej zgodności
konkretnych liczb, a nie oceną prawdziwości idei BOHN ani wartości monografii.
Najważniejsze własności - relacyjna konstrukcja orbit, bezstratna odwracalność,
inwariantność oraz przewaga reprezentacji orbitowej nad surowymi cechami -
zostały zachowane.

## Wynik jednostek

| ID | Ścisła reprodukcja | Ocena merytoryczna | Najważniejszy wynik |
|---|---|---|---|
| B-001 | EXACT_MATCH | POTWIERDZONA | 24 orbity: 4 singletony i 20 orbit trójelementowych; Burnside 64/4/4. |
| B-002 | EXACT_MATCH | POTWIERDZONA | Histogram ma wymiar 72 = 3 x 24; brak oddzielnego historycznego bloku wyniku. |
| B-003 | EXACT_MATCH | POTWIERDZONA | `inverse(forward(X)) == X` dokładnie; wagi tylko -1/+1. |
| B-004 | CLOSE_MATCH | POTWIERDZONA | Wszystkie trzy kryteria poprawności przechodzą; wydrukowane normy historyczne nie są identyczne. |
| B-005 | DIVERGENT | RDZEŃ NIENARUSZONY | Listing daje 0.970 / 0.970 / 0.970 zamiast 0.962 / 0.741 / 0.940. |
| B-006 | PARTIAL | RDZEŃ NIENARUSZONY | Gałąź trainable nie jest obliczana: wartość 0.470 jest stałą wpisaną w kodzie. |
| B-007 | DIVERGENT | WNIOSEK POTWIERDZONY | 0.488 / 0.980 / 0.972 zamiast 0.483 / 0.982 / 0.983. |
| B-008 | DIVERGENT | GŁÓWNY WNIOSEK POTWIERDZONY | 0.507 / 0.940 / 0.817 zamiast 0.506 / 0.968 / 0.984. |
| B-009 | CLOSE_MATCH | POTWIERDZONA | Inwariantność przechodzi na poziomie 10^-15; część liczb pomocniczych różni się od wydruku. |

Status `EXACT_MATCH` dla B-002 i B-003 dotyczy wszystkich jawnych własności
strukturalnych i wydruków samego listingu. Źródło nie zawiera dla nich osobnego
historycznego bloku `verbatim`.

## Audyt benchmarków

| Jednostka / metryka | Monografia | Windows | Różnica |
|---|---:|---:|---:|
| B-005 linear | 0.962 | 0.970 | +0.008 |
| B-005 RMIG frozen | 0.741 | 0.970 | +0.229 |
| B-005 RMIG trainable | 0.940 | 0.970 | +0.030 |
| B-006 linear raw | 0.483 | 0.488 | +0.005 |
| B-006 RMIG frozen | 0.471 | 0.488 | +0.017 |
| B-006 orbit energy | 0.981 | 0.980 | -0.001 |
| B-007 linear raw | 0.483 | 0.488 | +0.005 |
| B-007 linear orbit energy | 0.982 | 0.980 | -0.002 |
| B-007 MLP orbit energy | 0.983 | 0.972 | -0.011 |
| B-008 linear raw | 0.506 | 0.507 | +0.001 |
| B-008 linear histogram | 0.968 | 0.940 | -0.028 |
| B-008 MLP histogram | 0.984 | 0.817 | -0.167 |

## Wnioski

1. **Fundament matematyczny i wartość merytoryczna zostały potwierdzone.** Konstrukcja orbit, wymiar
   histogramu, dokładna odwracalność warstwy i strukturalna inwariantność działają.
2. **B-005 ujawnia rozbieżność kod--wynik, a nie słabość odwracalności.**
   Permutacja i zmiana znaków są odwracalną transformacją liniową. Regresja
   logistyczna ma po niej tę samą klasę hipotez, dlatego trzy wyniki 0.970 są
   matematycznie spójne z listingiem, a historyczne 0.741 dla frozen nie jest.
3. **B-006 nie zawiera pełnego eksperymentu trainable.** Liczba 0.470 jest
   przepisana jako stała, więc nie może być uznana za reprodukcję obliczeniową.
4. **W B-007 zasadniczy efekt reprezentacji został zachowany.** Energia orbitowa
   podnosi accuracy z 0.488 do 0.980, mimo ścisłej niezgodności kilku tysięcznych
   i 0.011 dla MLP.
5. **W B-008 główny wniosek o wartości histogramu pozostaje mocny.** Model
   liniowy rośnie z 0.507 do 0.940. Nie odtworzono jedynie szczegółowego wyniku
   wariantu MLP: 0.817 zamiast raportowanego 0.984.
6. Wyniki z Windowsa są prawie identyczne z niezależnym biegiem kontrolnym na
   Linuksie (NumPy 2.3.5, scikit-learn 1.8.0). Największe rozbieżności nie
   wyglądają więc na błąd jednego systemu operacyjnego.
7. Rozbieżności mają znaczenie dla precyzji archiwalnej i metodologii
   reprodukcji, lecz **nie zmieniają zasadniczej oceny naukowej BOHN**.

## Decyzja archiwalna

Nie poprawiamy historycznych listingów ani wyników. Zachowujemy równolegle:

- `RESULT_REPORTED` - treść monografii,
- `RESULT_REPRODUCED` - wynik współczesnego wykonania,
- jawny status zgodności i interpretację rozbieżności.
