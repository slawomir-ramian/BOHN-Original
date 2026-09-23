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

Kolejność źródłowa jest zapisana niezależnie od numeracji ID w
`inventory/source_chronology.csv`. Po Etapach 03 i 04 wykonano 20 ze 115
jednostek; 95 pozostaje do odtworzenia.

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

## Źródło kanoniczne

Źródło główne: `docs/source/BOHN_PL.pdf`.

Źródło pomocnicze: `docs/source/BOHN_EN_SOURCE.tex`.

SHA-256 dokumentu znajduje się w `docs/CANONICAL_SOURCE.md`.

## Najważniejsza zasada

Wynik raportowany w monografii (`RESULT_REPORTED`) nigdy nie jest nadpisywany
wynikiem nowego uruchomienia (`RESULT_REPRODUCED`).
