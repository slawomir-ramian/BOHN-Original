# ASD-001R FULL — zamrożony protokół potwierdzający

## Cel

Pełny eksperyment sprawdza, czy po jawnej korekcie generatora etykiet na
zależny od obu deklarowanych symetrii można odtworzyć strukturę tabeli 4.2:
`Top1 True = 10/10`, obie symetrie w `Top10 = 10/10` oraz średnie rangi 1 i 2.

Jest to równoległy eksperyment uzupełniający. Nie zastępuje historycznego
`ASD-001`, nie zmienia jego źródła i nie jest dodatkową pozycją w chronologii
115 jednostek PDF-a.

## Zamrożenie przed biegiem

Kod `two_symmetry_protocol.py` został zamrożony po pilocie 6/6 i przed użyciem
seedów potwierdzających. Jego SHA-256 oraz wszystkie parametry znajdują się w
`ASD-001R_PROTOCOL_LOCK.json`. Runner odmawia rozpoczęcia, jeżeli suma kodu nie
zgadza się z blokadą.

## Pełna konfiguracja

| Parametr | Wartość |
|---|---|
| Dane | `sklearn.datasets.load_digits` |
| C | `0.02, 0.05, 0.10, 0.20` |
| Seedy | `0–9` |
| Kandydaci | 2 prawdziwych + 97 losowych |
| Dopasowania | 40 |
| Solver | SAGA, czysta L1 (`l1_ratio=1.0`) |
| `max_iter` | 5000 |
| Równoległość | maksymalnie 2 procesy |

## Kryterium potwierdzenia strukturalnego

Status `STRUCTURAL_RECONSTRUCTION_CONFIRMED` wymaga jednocześnie:

- ukończenia 40/40 dopasowań;
- `Top1 True = 10/10` dla każdego `C`;
- obu prawdziwych symetrii w Top10 w 10/10 prób dla każdego `C`;
- średniej najlepszej rangi 1.0 i najgorszej 2.0 dla każdego `C`;
- dodatniej ważności obu symetrii i dodatniego marginesu nad najlepszym
  kandydatem losowym w 40/40 prób;
- dodatniego zysku połączenia obu sygnałów w kontroli ablacyjnej;
- braku ostrzeżeń o niezbieżności.

Dokładność jest porównywana z tabelą, lecz nie jest warunkiem potwierdzenia
strukturalnego. Zmieniony generator definiuje inny, jawnie oznaczony protokół.

## Dozwolony wniosek

Po sukcesie wolno stwierdzić, że zasadnicza teza publikacji — możliwość
autonomicznego znalezienia dwóch symetrii rzeczywiście kodujących etykietę —
została potwierdzona w równoległym eksperymencie uzupełniającym.

Nie wolno twierdzić, że odzyskano nieopublikowany kod ani że uzyskano
historyczne `EXACT_MATCH`.
