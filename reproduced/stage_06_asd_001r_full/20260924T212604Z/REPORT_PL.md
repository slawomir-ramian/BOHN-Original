# ASD-001R FULL — raport eksperymentu uzupełniającego

**Werdykt: STRUCTURAL_RECONSTRUCTION_CONFIRMED.**

Eksperyment używa zamrożonego, jawnie poprawionego generatora dwóch
symetrii. Nie jest historycznym `EXACT_MATCH` i nie zastępuje ASD-001.

| C | Accuracy | Tabela | Delta | Top1 True | Obie Top10 | Obie Top2 | Śr. best | Śr. worst | Min. margines |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.9169 | 0.9244 | 0.0075 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 | 0.3109 |
| 0.05 | 0.9331 | 0.9554 | 0.0223 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 | 0.5629 |
| 0.10 | 0.9337 | 0.9630 | 0.0293 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 | 0.7147 |
| 0.20 | 0.9230 | 0.9630 | 0.0400 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 | 0.8055 |

## Interpretacja

Potwierdzenie strukturalne oznacza, że dwie symetrie rzeczywiście użyte
do generowania etykiet są autonomicznie identyfikowane wśród 99
kandydatów zgodnie ze strukturą rang tabeli 4.2.

Różnice dokładności są raportowane oddzielnie i nie mogą być ukryte.
Pełne dane każdego dopasowania znajdują się w `results.json`.
