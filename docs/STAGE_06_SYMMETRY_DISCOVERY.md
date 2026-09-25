# Etap 06: wykrywanie symetrii

## Zakres i chronologia

Etap obejmuje następny ciągły fragment monografii, bez sortowania po ID:

| Pozycja w PDF | ID | Listing | Wynik historyczny |
|---:|---|---:|---|
| 29 | SD-001 | 41 | `verbatim` 9 |
| 30 | SD-002 | 42 | `verbatim` 10 |
| 31 | SD-003 | 43 | `verbatim` 11 |
| 32 | SD-004 | 44 | `verbatim` 12 |
| 33 | ASD-001 | 45 | tabela 4.2 (`tab:l1summary`) |

Każdy listing został wyodrębniony z `BOHN_EN_SOURCE.tex` i sprawdzony
hashem z audytu. Pełny runner uruchamia plik `historical/source_from_monograph.py`
bez ingerencji w kod. Sondy smoke są osobnymi, lżejszymi kontrolami.

## Znaczenie jednostek

- `SD-001` sprawdza kandydatów przesunięć dla danych z symetrią.
- `SD-002` jest kontrolą ujemną z losowymi etykietami.
- `SD-003` identyfikuje ukrytą symetrię odbicia poziomego.
- `SD-004` identyfikuje ukrytą symetrię obrotu o 180 stopni.
- `ASD-001` uczy rzadki model rangowania kandydatów.

## Ważna uwaga do ASD-001

Narracja i tabela 4.2 opisują dwie prawdziwe symetrie: odbicie i obrót o 180
stopni. W historycznej funkcji `make_labels` etykieta jest jednak skonstruowana
wyłącznie z asymetrii obrotu o 180 stopni. Wysoka pozycja odbicia może więc
wynikać z korelacji występujących w zbiorze cyfr. Repozytorium zachowuje ten
fakt jawnie i nie poprawia go po cichu.

Historyczny klasyfikator z solverem `saga` nie otrzymał `random_state`
(losowość podziału danych jest ustawiona osobno). Dlatego małe różnice
numeryczne między uruchomieniami są dopuszczalne, o ile zachowany jest wniosek
merytoryczny i rangi kandydatów.

## Czas wykonania

`ASD-001` jest znacznie cięższy od pozostałych jednostek. Runner wysyła
neutralny heartbeat co 60 sekund i zapisuje checkpoint po każdej jednostce.
Czerwony kolor w skryptach PowerShell pozostaje zarezerwowany dla rzeczywistych
błędów; komunikaty `PASS` są zielone.

### Odzyskanie po limicie czasu

Pierwszy lokalny pełny przebieg na czterech procesorach ukończył około 35 z 40
dopasowań ASD-001, po czym osiągnął techniczny limit 14 400 sekund. Adapter
`tools/run_asd_001_recovery.py` zachowuje algorytm historyczny, ale zapisuje
checkpoint po każdym dopasowaniu i uruchamia najwyżej dwa zadania równolegle.
Nie zmienia ani nie nadpisuje pliku `historical/source_from_monograph.py`.

Pełna lokalna reprodukcja zakończyła 40/40 dopasowań. Symetria `rotate_180`,
która faktycznie tworzy etykiety, była najlepsza w 40/40 prób. Odbicie poziome
nie odtworzyło raportowanej pozycji w Top10, dlatego wynik jest klasyfikowany
jako `PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH`. Szczegółowa analiza znajduje
się w `docs/STAGE_06_LOCAL_ANALYSIS.md`.

## Eksperyment uzupełniający ASD-001R

Po ujawnieniu niespójności zaprojektowano osobny generator, w którym zarówno
`flip_horizontal`, jak i `rotate_180` rzeczywiście uczestniczą w etykiecie.
Protokół zamrożono po pilocie, a następnie wykonano pełne 40 dopasowań z 97
kandydatami losowymi.

Obie prawdziwe symetrie zajęły miejsca 1 i 2 w 40/40 prób, miały dodatni
margines nad najlepszym losowym blokiem i przeszły kontrolę ablacyjną. Status:
`STRUCTURAL_RECONSTRUCTION_CONFIRMED`. Różnice accuracy względem tabeli są
zachowane jako `DIFFERENCE_AFTER_CORRECTION`. Szczegóły:
`docs/STAGE_06_ASD_001R_FULL_ANALYSIS.md`.

ASD-001R nie zastępuje ASD-001 i nie zmienia chronologii 115 jednostek PDF-a.
Jest rejestrowany osobno w `inventory/supplementary_experiments.csv`.
