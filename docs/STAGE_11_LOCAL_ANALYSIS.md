# Etap 11 — analiza pełnej rekonstrukcji lokalnej

## Zakres i granica źródłowa

Pełny bieg z `2026-09-27T16:11:44Z` objął pozycje 83--87 źródłowej
chronologii PDF-a: `AD-001`, `AD-002`, `AD-003`, `CL-001` i `CL-002`.
Wszystkie jednostki zakończyły wykonanie statusem `PASS`, a manifest SHA-256
wyników jest zgodny.

Listingi 58 i 59 są fragmentami: publikują architektury, przygotowanie danych
i fazę bazową, lecz właściwe fazy adaptacji oraz continual learning pozostawiają
w komentarzach. Dlatego wykonano jawną rekonstrukcję
`STAGE_11_RECONSTRUCTION_V1`. Historyczne fragmenty nie zostały zmodyfikowane,
a rekonstrukcja nie jest przedstawiana jako odzyskany kod historyczny.

Środowisko wykonania: Windows 10, Python 3.14.5, PyTorch 2.14.0+cpu i cztery
wątki obliczeniowe. Niepuste pliki `stderr` programu listing 58 zawierają paski
postępu pobierania zbiorów, a nie wyjątki ani awarie.

## Klasyfikacja jednostek

| ID | Status | Zachowanie wniosku | Maksymalna różnica |
|---|---|---:|---:|
| `AD-001` | `NUMERIC_DIFFERENCE` | nie | 29,80 pp |
| `AD-002` | `CONCLUSION_MATCH` | tak | 38,31 pp |
| `AD-003` | `CONCLUSION_MATCH` | tak | 23,70 pp |
| `CL-001` | `CLOSE_NUMERIC_MATCH` | tak | 3,30 pp |
| `CL-002` | `CONCLUSION_MATCH` | tak | 16,34 pp |

Statusy opisują zgodność naukową jawnej rekonstrukcji. `PASS` wykonania nie
oznacza automatycznie zgodności z tabelą.

## AD-001 — Perm+Head

Największa rozbieżność dotyczy adaptacji MNIST do Fashion-MNIST przy 500
przykładach:

| Metoda | Publikacja | Rekonstrukcja | Różnica |
|---|---:|---:|---:|
| Perm+Head | 51,4% | 21,6% | -29,8 pp |
| Head only | 48,0% | 22,3% | -25,7 pp |
| Perm only | 8,4% | 7,8% | -0,6 pp |
| Full tune | 67,2% | 59,3% | -7,9 pp |
| MLP head | 38,0% | 15,3% | -22,7 pp |
| MLP full | 76,3% | 70,7% | -5,6 pp |

Rekonstrukcja potwierdza, że sama permutacja pozostaje blisko poziomu losowego,
ale nie odtwarza wyraźnej korzyści wspólnego uczenia Perm+Head nad Head only.
Przy 500 próbkach Perm+Head jest nawet niższy o 0,7 pp. Przy 2000 i 5000
próbkach wartości Perm+Head są znacznie bliższe publikacji: odpowiednio
56,4% wobec 57,9% oraz 61,5% wobec 64,7%.

Wynik nie obala mechanizmu BOHN. Ogranicza konkretną tezę o przewadze
few-shot i wskazuje, że brakujące parametry fazy adaptacyjnej są materialne.

## AD-002 i AD-003 — większy model

Wartości bezwzględne rekonstrukcji są niższe od tabeli. Największa różnica
wynosi 38,31 pp dla `SBOHN full-tune` przy 100 przykładach: 52,24% w publikacji
wobec 13,93% lokalnie. Zachował się jednak kierunek efektu: wraz z liczbą
przykładów wyniki Head only i Full tune rosną, a przy 500 przykładach osiągają
48,33% i 50,70%.

Test modularności `AD-003` został zachowany: Head only osiąga 95,3% jakości
Full tune przy 500 próbkach, przekraczając zamrożony próg 85%.

## CL-001 i CL-002 — continual learning

Najważniejsza własność strukturalna odtworzyła się w obu programach:

| Jednostka | SBOHN przed | SBOHN po przywróceniu | Degradacja SBOHN | Degradacja MLP |
|---|---:|---:|---:|---:|
| `CL-001` | 72,90% | 72,90% | 0,00 pp | 69,90 pp |
| `CL-002` | 89,86% | 89,86% | 0,00 pp | 41,40 pp |

Zapisanie i ponowne załadowanie modułu zadaniowego dokładnie przywróciło wynik,
podczas gdy sekwencyjnie dostrajany MLP utracił część jakości na wcześniejszym
zadaniu.

## Wniosek końcowy

Cztery z pięciu jednostek zachowują główny wniosek naukowy. Jedna jednostka,
`AD-001`, pozostaje jawnym wynikiem `NUMERIC_DIFFERENCE`. Etap potwierdza
modularne przywracanie zadania i brak degradacji SBOHN, lecz nie daje podstaw
do uznania silnej przewagi Perm+Head w few-shot za niezależnie odtworzoną.

Po zamknięciu Etapu 11 ukończonych jest 87 ze 115 kanonicznych jednostek PDF-a;
pozostaje 28.
