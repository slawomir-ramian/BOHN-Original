# ASD-001R — jawna rekonstrukcja hipotezy dwóch symetrii

Ten katalog **nie jest częścią historycznego kodu ASD-001** i nie dodaje nowej
jednostki do 115 pozycji monografii. Jest oddzielnym eksperymentem
rekonstrukcyjnym, zaprojektowanym po wykryciu niespójności kod–tabela.

## Hipoteza

Tabela 4.2 mogła pochodzić z wcześniejszej lub innej wersji programu, w której
etykieta zależała zarówno od `flip_horizontal`, jak i `rotate_180`. Nie mamy
źródła potwierdzającego tę wersję, dlatego jest to hipoteza do sprawdzenia.

## Jedyna zmiana merytoryczna

Historyczne `make_labels` używa wyłącznie `rotate_180`. W ASD-001R wynik dwóch
niezależnych projekcji:

- `abs(X - flip_horizontal(X))`,
- `abs(X - rotate_180(X))`

jest standaryzowany do jednakowej wariancji i sumowany przed progowaniem
medianą. Dzięki temu obie deklarowane symetrie naprawdę uczestniczą w
mechanizmie etykiety.

## Ochrona przed artefaktami

- kandydaci są tasowani deterministycznie dla każdego seedu i `C`;
- współczynniki zerowe są oznaczone jako remis nierozstrzygnięty;
- raport zawiera surowe ważności i margines nad najlepszym blokiem losowym;
- pilot używa seedów `100–102`, innych niż historyczne `0–9`;
- pilot jest zawsze oznaczony `PILOT_NON_CONFIRMATORY`.

Kod historyczny pozostaje w `../historical/source_from_monograph.py` bez zmian.

## Pełne potwierdzenie

Po pozytywnym pilocie protokół został zamrożony w
`ASD-001R_PROTOCOL_LOCK.json`. Pełny bieg używa seedów `0–9`, wszystkich
czterech wartości `C` i 97 kandydatów losowych. Prerejestracja znajduje się w
`docs/STAGE_06_ASD_001R_FULL_PREREGISTRATION.md`.

Pełny bieg zakończył się statusem `STRUCTURAL_RECONSTRUCTION_CONFIRMED`:
obie symetrie zajęły rangi 1 i 2 w 40/40 prób wśród 99 kandydatów. Wyniki są w
`reproduced/stage_06_asd_001r_full/20260924T212604Z/`, a analiza w
`docs/STAGE_06_ASD_001R_FULL_ANALYSIS.md`.
