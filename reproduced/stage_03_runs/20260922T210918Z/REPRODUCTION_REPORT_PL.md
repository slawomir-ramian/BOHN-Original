# Raport reprodukcji Etapu 03

Uruchomienie UTC: `2026-09-22T21:09:18+00:00`.

| ID | Status | Uwagi |
|---|---|---|
| B-001 | EXACT_MATCH |  |
| B-002 | VERIFIED_NO_REFERENCE_BLOCK |  |
| B-003 | VERIFIED_NO_REFERENCE_BLOCK |  |
| B-004 | CLOSE_MATCH | Zgodność kryteriów PASS; wartości zmiennoprzecinkowe zależą od środowiska. |
| B-005 | DIVERGENT | Odwracalne przestawienie i zmiana znaków zachowują klasę modeli liniowych; listing daje identyczne predykcje dla trzech wariantów w tym środowisku. |
| B-006 | PARTIAL | W listingu wartość RMIG trainable = 0.470 jest wpisana na stałe i nie jest obliczana; dlatego reprodukcja pozostaje PARTIAL. |
| B-007 | DIVERGENT |  |
| B-008 | DIVERGENT |  |
| B-009 | CLOSE_MATCH | Zgodność kryteriów inwariantności; dokładny błąd maszynowy zależy od NumPy/platformy. |

## Interpretacja

`DIVERGENT` nie oznacza automatycznie błędu nowego runnera. Oznacza, że wynik
otrzymany z opublikowanego listingu nie zgadza się z wartością wydrukowaną
w monografii w przyjętej dokładności. Szczegóły liczbowe są w `results.json`.

Wyniki raportowane pozostają nietknięte w katalogach `historical/`; ten raport
zawiera wyłącznie nową reprodukcję.
