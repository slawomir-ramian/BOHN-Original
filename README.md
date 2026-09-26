# BOHN-Original

Historyczne i reprodukowalne archiwum rozwoju BOHN/SBOHN opisanego w monografii
Sławomira Ramiana z czerwca 2026 r.

## Cel

Repozytorium ma lokalnie zachować wszystkie programy, benchmarki, testy,
eksperymenty, warianty, wyniki dodatnie i ujemne oraz interpretacje obecne w
monografii. Oryginalne wyniki wykonane w chmurze pozostają oddzielone od nowych
wyników reprodukcji lokalnej.

## Stan

Etap 03 zakończony - uruchamialna rekonstrukcja i lokalna reprodukcja fundamentu
`B-001`--`B-009`. Oryginalne Listingi A.1--A.9 i historyczne wydruki są
przechowywane oddzielnie od technicznych adapterów i nowych wyników lokalnych.
Wartość merytoryczna fundamentu została potwierdzona. W technicznym audycie
ścisłej zgodności liczb odnotowano trzy `EXACT_MATCH`, dwa `CLOSE_MATCH`, trzy
`DIVERGENT` i jeden `PARTIAL`; statusy te nie są oceną teorii. Szczegóły:
`docs/STAGE_03_LOCAL_ANALYSIS.md`. Plik
`inventory/experiments.csv` zawiera pełny rejestr 115 jednostek, a
`docs/EXPERIMENT_INDEX.md` jest jego wersją czytelną.

Etap 04 zakończony - odtworzono pełny rozdział SBOHN (`S-001`--`S-011`)
zgodnie z chronologią PDF-a. Cztery jednostki mają `EXACT_MATCH`, dwie
`CLOSE_MATCH`, dwie `REPORTED_SUPERSET_MATCH`, a implementacja `S-010`
przechodzi kontrakt wymiaru `64 -> 192`. `S-001` pozostaje jawnie
niedeterministycznym testem pojedynczym, a w `S-004` zachowano historyczny błąd
licznika wydruku. Główne wyniki SBOHN, odporność i wykrywanie ukrytej
symetrii zostały potwierdzone. Szczegóły: `docs/STAGE_04_LOCAL_ANALYSIS.md`.

Etap 05 zakończony - odtworzono następny ciągły fragment PDF-a: `G-001` oraz
`SO-001`--`SO-007`. Historyczny adaptacyjny router Fishera dał dokładnie ten
sam wydruk, a własności matematyczne uogólnienia SBOHN na ciągłą grupę SO(2)
zostały potwierdzone. `SO-005` i `SO-006` pozostają jawnie częściowymi
rekonstrukcjami, ponieważ monografia nie publikuje pełnego generatora danych
ani protokołu. Mimo różnic surowych baz odniesienia główny wynik SO(2)-SBOHN
wynosi w obu przypadkach `1.000`, zgodnie z monografią. Szczegóły:
`docs/STAGE_05_LOCAL_ANALYSIS.md`.

Etap 06 obejmuje następny ciągły fragment PDF-a: `SD-001`--`SD-004` oraz
`ASD-001`. Wszystkie pięć jednostek ma pełny, niezmieniony kod historyczny
i zapisany wynik odniesienia. Szybkie sondy smoke są technicznie oddzielone od
pełnego wykonania. `SD-001`--`SD-004` uzyskały `CLOSE_NUMERIC_MATCH`. W
`ASD-001` odtworzono odkrycie symetrii faktycznie kodującej etykiety w 40/40
prób, natomiast druga symetria deklarowana w tabeli nie jest użyta przez
historyczne `make_labels`; status to
`PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH`. Szczegóły:
`docs/STAGE_06_LOCAL_ANALYSIS.md`.

Osobno przygotowano `ASD-001R`, jawny pilot hipotezy, że tabela 4.2 mogła
powstać z wersji generatora etykiet zależnej od obu deklarowanych symetrii.
Nie jest to historyczna jednostka ani dowód istnienia takiej wersji kodu.
Projekt: `docs/STAGE_06_ASD_001R_DESIGN.md`.

Pilot ASD-001R przeszedł kryteria strukturalne w 6/6 prób. Przed pełnym biegiem
zamrożono kod i kryteria eksperymentu uzupełniającego obejmującego 40
dopasowań oraz pełne 97 kandydatów losowych. Prerejestracja:
`docs/STAGE_06_ASD_001R_FULL_PREREGISTRATION.md`.

Pełny ASD-001R zakończył 40/40 dopasowań i odtworzył rangi 1--2 obu prawdziwych
symetrii wśród 99 kandydatów dla każdego `C`. Status
`STRUCTURAL_RECONSTRUCTION_CONFIRMED` stanowi uzupełniające potwierdzenie
mechanizmu publikacji. Nie jest to historyczne `EXACT_MATCH`; dokładności
różnią się od tabeli o `0.0075`--`0.0400`. Szczegóły:
`docs/STAGE_06_ASD_001R_FULL_ANALYSIS.md`.

Etap 07 zakończony - odtworzono cały rozdział 5 (`PL-001`--`CMP-002`) na
pozycjach 34--45 PDF-a. Siedem jednostek z pełnym kodem wykonano historycznie:
cztery uzyskały `CLOSE_NUMERIC_MATCH`, a trzy `CONCLUSION_MATCH`. Pięć
jednostek bez opublikowanego programu zachowano jako
`AUDITED_REPORTED_RESULT`, bez przedstawiania rekonstrukcji jako kodu
historycznego. Szczegóły: `docs/STAGE_07_LOCAL_ANALYSIS.md`.

Etap 07R jest oddzielnym, zamrożonym eksperymentem uzupełniającym dla pięciu
jednostek `NARRATIVE_ONLY`. Cztery rekonstrukcje uzyskały
`STRUCTURAL_RECONSTRUCTION_CONFIRMED`. `HD-003R` zachował dodatnią, malejącą
z wymiarem średnią przewagę SBOHN, lecz nie spełnił ostrzejszego kryterium
wygranej w każdym seedzie przy `d=1023` i `d=4095`; status całego biegu to
`PARTIAL_SUPPLEMENTARY_CONFIRMATION`. Szczegóły:
`docs/STAGE_07R_FULL_ANALYSIS.md`.

Etap 08 zakończony - wykonano pozycje 46--56 rozdziału 6: Learnable SBOHN
i Log-Domain Sinkhorn. `LS-001` oraz `LD-001`--`LD-005` uzyskały
`CLOSE_NUMERIC_MATCH`; największa różnica wobec tabeli wyniosła `0.00226`.
Wspólny listing 53 wykonuje pipeline `LS-001`, ale nie zawiera kodu
zaawansowanych eksperymentów `LS-002`--`LS-006`. Te pięć pozycji zachowano
uczciwie jako `AUDITED_REPORTED_RESULT`, bez udawania lokalnej reprodukcji.
Szczegóły: `docs/STAGE_08_LOCAL_ANALYSIS.md`.

Etap 09 zakończony - wykonano pozycje 57--72 rozdziału 7: Fractal SBOHN,
Patch SBOHN i wyniki wysokiej rozdzielczości. Wszystkie sześć jednostek z
kompletnym kodem (`FR-002`, `FR-003`, `PT-001`, `PT-002`, `PT-004`,
`PT-005`) uzyskało `CLOSE_NUMERIC_MATCH`. Wartości Fractal SBOHN były
identyczne z publikacją, a największa różnica w wynikach Patch SBOHN wyniosła
`2.67e-08`. Pozostałe dziesięć pozycji zachowano jako
`AUDITED_REPORTED_RESULT`, ponieważ PDF nie publikuje ich kompletnego kodu
docelowego. Szczegóły: `docs/STAGE_09_LOCAL_ANALYSIS.md`.

Kolejność źródłowa jest zapisana niezależnie od numeracji ID w
`inventory/source_chronology.csv`. Etap 06 zajmuje pozycje 29--33, Etap 07
pozycje 34--45, Etap 08 pozycje 46--56, a Etap 09 pozycje 57--72, dokładnie
tak jak w PDF-ie. Po Etapach 03--09 przygotowano 72 ze 115 jednostek; 43 pozostają do
odtworzenia. Eksperymenty z sufiksem `R`
nie zwiększają tej liczby, ponieważ należą do osobnego rejestru uzupełniającego.

Audyt obejmuje 94 numerowane tabele, 44 podpisane listingi PDF, 74 środowiska
`lstlisting`, 20 bloków `verbatim` oraz 24 wieloeksperymentalne zestawy kodu.

## Uruchomienie Etapu 03

```powershell
.\SETUP_STAGE_03.ps1
.\RUN_STAGE_03_SMOKE.ps1
.\RUN_STAGE_03_FULL.ps1
```

Pełna instrukcja: `INSTALL_STAGE_03.md`.

## Uruchomienie Etapu 04

```powershell
.\SETUP_STAGE_04.ps1
.\RUN_STAGE_04_SMOKE.ps1
.\RUN_STAGE_04_FULL.ps1
```

Pełna instrukcja: `INSTALL_STAGE_04.md`.

## Uruchomienie Etapu 05

```powershell
.\SETUP_STAGE_05.ps1
.\RUN_STAGE_05_SMOKE.ps1
.\RUN_STAGE_05_FULL.ps1
```

Pełna instrukcja: `INSTALL_STAGE_05.md`.

## Uruchomienie Etapu 06

```powershell
.\SETUP_STAGE_06.ps1
.\RUN_STAGE_06_SMOKE.ps1
.\RUN_STAGE_06_FULL.ps1
```

Pełna instrukcja: `INSTALL_STAGE_06.md`.

## Uruchomienie Etapu 07 i 07R

```powershell
.\SETUP_STAGE_07.ps1
.\RUN_STAGE_07_SMOKE.ps1
.\RUN_STAGE_07_FULL.ps1
.\SETUP_STAGE_07R.ps1
.\RUN_STAGE_07R_PILOT.ps1
.\RUN_STAGE_07R_FULL.ps1
```

Instrukcje: `INSTALL_STAGE_07.md` oraz `INSTALL_STAGE_07R.md`.

## Uruchomienie Etapu 08

```powershell
.\SETUP_STAGE_08.ps1
.\RUN_STAGE_08_SMOKE.ps1
.\RUN_STAGE_08_FULL.ps1
```

Pełna instrukcja: `INSTALL_STAGE_08.md`.

## Uruchomienie Etapu 09

```powershell
.\SETUP_STAGE_09.ps1
.\RUN_STAGE_09_SMOKE.ps1
.\RUN_STAGE_09_FULL.ps1
```

Etap 09 obejmuje 16 pozycji rozdziału 7 w kolejności PDF-a. Sześć jednostek
ma kompletny kod wykonywalny w dwóch wspólnych programach, a dziesięć pozostaje
jawnym audytem opublikowanych wyników. Pełna instrukcja: `INSTALL_STAGE_09.md`.

## Źródło kanoniczne

Źródło główne: `docs/source/BOHN_PL.pdf`.

Źródło pomocnicze: `docs/source/BOHN_EN_SOURCE.tex`.

SHA-256 dokumentu znajduje się w `docs/CANONICAL_SOURCE.md`.

## Najważniejsza zasada

Wynik raportowany w monografii (`RESULT_REPORTED`) nigdy nie jest nadpisywany
wynikiem nowego uruchomienia (`RESULT_REPRODUCED`).
