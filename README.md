# BOHN-Original

Historyczne i reprodukowalne archiwum rozwoju BOHN/SBOHN opisanego w monografii
Sławomira Ramiana z czerwca 2026 r.

## Cel

Repozytorium ma lokalnie zachować wszystkie programy, benchmarki, testy,
eksperymenty, warianty, wyniki dodatnie i ujemne oraz interpretacje obecne w
monografii. Oryginalne wyniki wykonane w chmurze pozostają oddzielone od nowych
wyników reprodukcji lokalnej.

## Stan

Etap 02 - audyt krzyżowy PDF i źródłowego LaTeX-a. Kod eksperymentalny nie
został jeszcze wyodrębniony do osobnych modułów. Plik
`inventory/experiments.csv` zawiera 115 jednostek do odtworzenia, a
`docs/EXPERIMENT_INDEX.md` jest jego wersją czytelną.

Audyt obejmuje 94 numerowane tabele, 44 podpisane listingi PDF, 74 środowiska
`lstlisting`, 20 bloków `verbatim` oraz 24 wieloeksperymentalne zestawy kodu.

## Źródło kanoniczne

Źródło główne: `docs/source/BOHN_PL.pdf`.

Źródło pomocnicze: `docs/source/BOHN_EN_SOURCE.tex`.

SHA-256 dokumentu znajduje się w `docs/CANONICAL_SOURCE.md`.

## Najważniejsza zasada

Wynik raportowany w monografii (`RESULT_REPORTED`) nigdy nie jest nadpisywany
wynikiem nowego uruchomienia (`RESULT_REPRODUCED`).
