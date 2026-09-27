# Etap 12 — analiza lokalnego wykonania

## Wynik ogólny

Pełny bieg `20260927T184235Z` wykonał oba pełne historyczne listingi 60 i 61
bez modyfikowania ich treści. `SOTA-001` i `SOTA-002` zakończyły się kodem 0,
otrzymały dokładny kontrakt architektury (`EXACT_MATCH`) oraz zachowały główne
wnioski publikacji (`CONCLUSION_MATCH`).

Po zamknięciu etapu wykonano **89 ze 115** jednostek źródłowego PDF-a;
**26** pozostaje `NOT_RUN`.

## SOTA-001 — Fashion-MNIST

| Model | Publikacja [%] | Lokalnie [%] | Różnica [pp] | Parametry |
|---|---:|---:|---:|---:|
| MLP | 78,0 | 71,8 | -6,2 | 235 146 |
| ViT-Tiny | 66,6 | 69,0 | +2,4 | 71 946 |
| Fractal SBOHN v2 | 54,2 | 66,2 | **+12,0** | 54 298 |
| CNN | 35,2 | 38,0 | +2,8 | 23 946 |

Ranking MLP > ViT > SBOHN > CNN został zachowany. Największa różnica nie jest
pogorszeniem SBOHN: lokalny wynik modelu jest o 12 pp wyższy od tabeli.
Listing nie ustawia ziarna losowego, dlatego ścisłe odtworzenie dokładności
nie jest oczekiwane. Liczby parametrów i pamięć modeli zgadzają się z tabelą.

Komunikaty zapisane w `stderr` dla tego przebiegu są procentowym postępem
pierwszego pobrania Fashion-MNIST, a nie wyjątkiem programu.

## SOTA-002 — skalowanie

| Model | Wykładnik publikacji | Lokalnie | Różnica |
|---|---:|---:|---:|
| Fractal SBOHN v2 | 0,059 | -0,010 | 0,069 |
| CNN | 0,668 | 0,697 | 0,029 |
| ViT-Tiny | 0,040 | 0,043 | 0,003 |

Wniosek jest zachowany: wykładniki SBOHN i ViT są wyraźnie mniejsze od
wykładnika CNN. Przy 448 px lokalne czasy wyniosły odpowiednio 3,55 ms,
27,22 ms i 4,95 ms. Maksymalna różnica surowego czasu względem tabeli to
17,05 ms i dotyczy CNN przy 448 px. Jest to metryka zależna od sprzętu oraz
bardzo krótkiego historycznego protokołu z trzema pomiarami.

Liczby parametrów dla wszystkich pięciu rozdzielczości są dokładnie zgodne z
publikacją. Ujemny lokalny wykładnik SBOHN (-0,010) nie oznacza przyspieszania
asymptotycznego; przy tak krótkich pomiarach wskazuje praktycznie stały czas w
badanym zakresie.

## Wniosek merytoryczny

Etap nie ujawnił błędu architektury ani sprzeczności z ideą BOHN/SBOHN.
Potwierdził mały rozmiar modeli, zachował ranking porównania jakości oraz
kluczowy wniosek skalowania: konstrukcje o stałej liczbie patchy zachowują
znacznie łagodniejszy wzrost kosztu niż CNN w opublikowanym protokole.
