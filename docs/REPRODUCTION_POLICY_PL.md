# Polityka reprodukcji

## Dwie warstwy wyników

- `RESULT_REPORTED` - wynik zapisany w monografii, pochodzący z historycznego
  wykonania, zwykle w chmurze.
- `RESULT_REPRODUCED` - wynik uzyskany po współczesnym uruchomieniu lokalnej
  rekonstrukcji.

Wynik reprodukcji nigdy nie zastępuje wyniku raportowanego.

## Statusy reprodukcji

- `NOT_RUN` - eksperyment jeszcze nie został uruchomiony.
- `EXACT_MATCH` - wynik zgodny w granicach dokładności raportowanej w PDF.
- `CLOSE_MATCH` - niewielka różnica mieszcząca się w ustalonym progu.
- `DIVERGENT` - różnica istotna.
- `PARTIAL` - odtworzono tylko część baterii lub wariantów.
- `BLOCKED_MISSING_INFORMATION` - brak informacji uniemożliwia wierne wykonanie.
- `BLOCKED_RESOURCES` - wymagane zasoby przekraczają aktualne możliwości.

## Warstwy kodu

Każdy eksperyment docelowo otrzyma:

```text
experiment/
├── README_PL.md
├── provenance.json
├── historical/
│   ├── source_from_monograph.py
│   └── reported_results.*
├── runner/
│   └── run.py
├── reproduced/
│   ├── results.*
│   └── execution_metadata.json
└── REPRODUCTION_REPORT.md
```

`historical/` zachowuje materiał źródłowy. `runner/` może zawierać wyłącznie
techniczne dostosowania potrzebne do uruchomienia i musi dokumentować każdą
zmianę.

## Zakaz domysłów

Brakującego seedu, podziału danych, parametru, wersji biblioteki lub wyniku nie
uzupełniamy po cichu. Każde założenie trafia do `provenance.json` i raportu.

