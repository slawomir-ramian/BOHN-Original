# Etap 08 — raport wykonania

Jednostki wykonano w kolejności PDF-a. Wynik techniczny jest oddzielony od zgodności numerycznej.

| # | ID | Tryb | Wykonanie | Porównanie | Czas [s] |
|---:|---|---|---|---|---:|
| 1 | LS-001 | HISTORICAL_SOURCE | PASS | CLOSE_NUMERIC_MATCH | 409.344 |
| 2 | LS-002 | AUDITED_REPORTED_RESULT | PASS | AUDITED_REPORTED_RESULT | 0.000 |
| 3 | LS-003 | AUDITED_REPORTED_RESULT | PASS | AUDITED_REPORTED_RESULT | 0.000 |
| 4 | LS-004 | AUDITED_REPORTED_RESULT | PASS | AUDITED_REPORTED_RESULT | 0.000 |
| 5 | LS-005 | AUDITED_REPORTED_RESULT | PASS | AUDITED_REPORTED_RESULT | 0.000 |
| 6 | LS-006 | AUDITED_REPORTED_RESULT | PASS | AUDITED_REPORTED_RESULT | 0.000 |
| 7 | LD-001 | HISTORICAL_SOURCE | PASS | CLOSE_NUMERIC_MATCH | 584.492 |
| 8 | LD-002 | HISTORICAL_SOURCE_SHARED_RUN | PASS | CLOSE_NUMERIC_MATCH | 0.000 |
| 9 | LD-003 | HISTORICAL_SOURCE_SHARED_RUN | PASS | CLOSE_NUMERIC_MATCH | 0.000 |
| 10 | LD-004 | HISTORICAL_SOURCE | PASS | CLOSE_NUMERIC_MATCH | 676.413 |
| 11 | LD-005 | HISTORICAL_SOURCE_SHARED_RUN | PASS | CLOSE_NUMERIC_MATCH | 0.000 |

## Granica źródłowa

`LS-002`–`LS-006` mają tabele wynikowe, lecz przypisany wspólny listing 53 nie zawiera kodu tych pięciu eksperymentów. Dlatego zachowano je jako `AUDITED_REPORTED_RESULT`, bez tworzenia ukrytej rekonstrukcji.

`NUMERIC_DIFFERENCE` opisuje wynik naukowy i nie jest błędem wykonania programu.
