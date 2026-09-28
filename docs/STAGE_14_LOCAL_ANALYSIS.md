# Etap 14 — analiza lokalnego wykonania

## Wynik ogólny

Pełny bieg `20260928T180446Z` wykonał trzy kompletne programy historyczne
kodem 0. Sześć pozostałych pozycji ma status `AUDITED_REPORTED_RESULT`,
ponieważ opublikowane listingi nie zawierają pętli generujących odpowiadające
im tabele.

Spośród trzech wykonanych eksperymentów **1 z 3** zachował centralny wniosek,
a dwa wykazały istotne różnice liczbowe. Ocena Etapu 14 to zatem
**PARTIAL_REPRODUCTION**, mimo technicznego `PASS` wszystkich dziewięciu
jednostek.

Po closeoucie zakończono **108 ze 115** jednostek źródłowego PDF-a;
**7** pozostaje `NOT_RUN`.

## MOE-004 — Hard Assignment + Gate Distillation

| Domena | Accuracy publikacji | Accuracy lokalna | Routing do właściwego eksperta |
|---|---:|---:|---:|
| MNIST | 93,0% | 65,0% | 57,8% do E0 |
| Fashion | 87,4% | 73,0% | 71,2% do E1 |
| KMNIST | 87,2% | 81,8% | 98,8% do E2 |

Router wybiera właściwego eksperta jako najczęstszy wybór we wszystkich
trzech domenach, ale dla MNIST i Fashion nie odtwarza raportowanej niemal
idealnej specjalizacji 99,8%. Największa różnica względem tabeli wynosi
42,0 pp. Teza o pełnej specjalizacji i jakości gated nie została potwierdzona;
wynik ma status `NUMERIC_DIFFERENCE`.

## MOE-006 — Confidence Routing

| Metoda | Średnia publikacji | Średnia lokalna |
|---|---:|---:|
| Max logit | 76,2% | 71,4% |
| Confidence | 73,3% | 70,3% |
| Margin | 71,7% | 67,5% |

Zachowano centralny ranking **max-logit > confidence > margin**. Największa
jednostkowa różnica wynosi 10,7 pp, dlatego wynik jest `CONCLUSION_MATCH`, a
nie bliską zgodnością liczbową.

## MOE-008 — Hybrid BN/LN

| Domena | Gated publikacji | Gated lokalnie | Oracle lokalnie | Routing do właściwego eksperta |
|---|---:|---:|---:|---:|
| MNIST | 96,8% | 51,8% | 97,0% | 37,8% do E0 |
| Fashion | 89,0% | 54,6% | 84,2% | 55,2% do E1 |
| KMNIST | 85,6% | 84,0% | 84,0% | 99,4% do E2 |

Eksperci pozostają silni: średnia oracle wynosi 88,4%, a forgetting 0,0%.
Nie powiódł się jednak automatyczny routing, szczególnie dla MNIST. Średnia
gated spadła do 63,5%, a gate overhead wyniósł 24,9% zamiast raportowanego
0,0%. Największa różnica ma 62,2 pp. Główna teza o skutecznym, prawie
bezstratnym gate nie została odtworzona, więc wynik ma status
`NUMERIC_DIFFERENCE`.

## Granice źródłowe i integralność

Historyczne listingi 67--69 pozostały niezmienione. Warstwa zgodności
przekierowała wyłącznie absolutną ścieżkę `/tmp/data` do lokalnego cache.
Manifest SHA-256 pełnego biegu został zweryfikowany. Hotfix 01 zmienił jedynie
sposób odnajdywania tabel w dwujęzycznym LaTeX-u: zamiast tekstu podpisu używa
audytowanego numeru tabeli; nie zmienił kodu ani wyników.

## Wniosek merytoryczny

Etap 14 nie obala idei modularnych ekspertów BOHN. `MOE-006` zachowuje
przewidywany ranking bezparametrowych metod routingu, a `MOE-008` pokazuje
wysoką jakość oracle i zerowe zapominanie. Nie potwierdza jednak mocniejszej
tezy, że opublikowany gate niezawodnie rozpoznaje domenę i dorównuje oracle.
Repozytorium powinno prezentować ten etap jako częściową reprodukcję oraz
oddzielać jakość ekspertów od jakości routera.
