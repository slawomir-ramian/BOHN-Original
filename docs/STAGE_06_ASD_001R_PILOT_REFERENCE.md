# ASD-001R — referencyjny wynik pilota

## Zakres

Ten dokument zapisuje pierwszy bieg projektowy ASD-001R. Nie jest wynikiem
historycznym i nie stanowi potwierdzenia tabeli 4.2. Użyto wyłącznie seedów
pilota `100–102`, dwóch wartości `C` oraz 20 kandydatów losowych.

Środowisko biegu: Python 3.12.14, NumPy 2.3.5, scikit-learn 1.8.0.

## Wynik

| C | Sukces strukturalny | Obie prawdziwe Top2 | Accuracy | Średni gain ablacji |
|---:|---:|---:|---:|---:|
| 0.10 | 3/3 | 3/3 | 0.9525 | 0.2142 |
| 0.20 | 3/3 | 3/3 | 0.9519 | 0.2142 |

W każdym z sześciu dopasowań `flip_horizontal` miał rangę 1, a `rotate_180`
rangę 2. Słabszy z dwóch prawdziwych bloków miał dodatni margines nad
najlepszym blokiem losowym. Nie wystąpiły ostrzeżenia solvera.

## Wniosek ograniczony

Pilot pokazuje, że po jawnej zmianie generatora etykiet na zależny od obu
symetrii metoda odzyskuje strukturę rang 1–2. Jest to zgodne z hipotezą o innej
wersji programu, ale jej nie dowodzi. Dokładne wartości tabeli nie zostały
odtworzone ani sprawdzane w tym pilocie.
