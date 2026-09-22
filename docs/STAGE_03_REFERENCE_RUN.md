# Kontrolne uruchomienie Etapu 03

Data: 2026-09-22. Środowisko kontrolne: Python 3.12.14, NumPy 2.3.5,
scikit-learn 1.8.0, Linux x86-64.

Najpierw wykonano sześć testów kontraktowych. Następnie wykonano sekwencyjnie
niezmienione Listingi A.1--A.9 oraz niezależnie adapter `run_stage_03.py`.
Adapter zwrócił te same wartości co listingi uruchomione bezpośrednio.

| ID | Wynik kontrolny | Status względem monografii |
|---|---|---|
| B-001 | 24 orbity; 4 singletony; 20 orbit potrójnych | EXACT_MATCH |
| B-002 | wymiar histogramu 72 | VERIFIED_NO_REFERENCE_BLOCK |
| B-003 | dokładna rekonstrukcja wejścia | VERIFIED_NO_REFERENCE_BLOCK |
| B-004 | trzy testy PASS | CLOSE_MATCH |
| B-005 | 0.970 / 0.970 / 0.970 | DIVERGENT |
| B-006 | 0.488 / 0.488 / 0.470 / 0.980 | PARTIAL |
| B-007 | 0.488 / 0.980 / 0.972 | DIVERGENT |
| B-008 | 0.507 / 0.943 / 0.817 | DIVERGENT |
| B-009 | test pojedynczy i batch: PASS | CLOSE_MATCH |

Rozbieżności są zachowane jako wynik audytu. Nie wprowadzono zmian do kodu
historycznego, aby dopasować go do wydruków w monografii. Inna wersja NumPy lub
scikit-learn może zmienić wyniki numeryczne, szczególnie MLP, lecz nie usuwa
strukturalnej obserwacji z `B-005` ani brakującego treningu w `B-006`.
