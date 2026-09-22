# Etap 03 - rekonstrukcja fundamentu BOHN

Zakres: `B-001`--`B-009`, czyli Listingi A.1--A.9.

## Warstwy

1. `historical/source_from_monograph.py` - kod wyodrębniony 1:1 z LaTeX-a.
2. `historical/reported_results.txt` - historyczny wydruk, jeśli w źródle
   istnieje oddzielny blok `verbatim`.
3. `src/bohn_original/foundation.py` - importowalny adapter techniczny.
4. `tools/run_stage_03.py` - kontrolowany runner i porównanie wyników.
5. `reproduced/stage_03_runs/` - nowe, lokalne wykonania.

Oryginał nie został poprawiony ani zastąpiony adapterem. Listing historyczny
zachowuje zależności od wcześniejszych listingów, ponieważ monografia ma w tym
miejscu formę sekwencyjnego notebooka.

## Krytyczny punkt audytu

W `B-006` wynik `RMIG trainable = 0.470` jest wpisany w listingu jako stała z
komentarzem „Result from the full experiment”. Opublikowany listing nie zawiera
obliczenia tej wartości. Z tego powodu `B-006` musi pozostać `PARTIAL` nawet,
gdy pozostałe liczby są zgodne.

W `B-005` wszystkie trzy reprezentacje są odwracalnymi przestawieniami i
zmianami znaków współrzędnych. Dla regresji logistycznej zachowują tę samą klasę
modeli. Runner celowo wykonuje listing bez korygowania tej własności; ewentualna
niezgodność z tabelą historyczną jest raportowana jako `DIVERGENT`.
