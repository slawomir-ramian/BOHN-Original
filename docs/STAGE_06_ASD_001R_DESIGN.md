# ASD-001R — projekt jawnego eksperymentu rekonstrukcyjnego

## Status epistemiczny

Istnieje bezpośrednia niespójność: opublikowany generator etykiet ASD-001 używa
tylko obrotu o 180°, natomiast tabela 4.2 ocenia jednocześnie obrót i odbicie
poziome jako dwie prawdziwe symetrie. Odzyskany dodatkowy plik źródłowy ma tę
samą logikę co listing monografii. Nie dowodzi to, że inna wersja programu nie
istniała.

ASD-001R sprawdza zatem jawną hipotezę: **czy struktura tabeli staje się
odtwarzalna, gdy etykieta rzeczywiście zależy od obu deklarowanych symetrii?**
Nie jest to próba przypisania autorowi nieopublikowanego kodu.

## Protokół pilota

| Parametr | Wartość |
|---|---|
| Zbiór | `sklearn.datasets.load_digits` |
| Seedy podziału | `100, 101, 102` |
| Wartości C | `0.10, 0.20` |
| Kandydaci | 2 prawdziwych + 20 losowych |
| Klasyfikator | `LogisticRegression`, SAGA, czysta L1 |
| Limit iteracji | 2500 |
| Kolejność bloków | tasowana deterministycznie |
| Charakter wyniku | `PILOT_NON_CONFIRMATORY` |

Pilot nie używa historycznych seedów `0–9`, aby nie służył do dopasowywania
procedury do opublikowanej tabeli.

## Kryteria strukturalne pilota

Każde dopasowanie jest oceniane oddzielnie. Sukces strukturalny wymaga:

1. obu prawdziwych bloków z dodatnią ważnością;
2. rang 1 i 2 dla obu prawdziwych bloków;
3. dodatniego marginesu słabszego prawdziwego bloku nad najlepszym losowym;
4. braku ostrzeżenia o braku zbieżności;
5. lepszej predykcji sygnału połączonego niż każdego składnika osobno.

Niespełnienie kryterium jest wynikiem badawczym, nie awarią techniczną.

## Następny krok po pilocie

Dopiero po zamrożeniu protokołu należy wykonać bieg potwierdzający z 97
kandydatami i seedami `0–9`, a także kontrole `flip-only`, `rotate-only` oraz
losowe etykiety. Nawet pełny sukces uzasadni wyłącznie zdanie, że strukturę
tabeli można odtworzyć po jawnej korekcie generatora dwóch symetrii. Nie będzie
dowodem, że właśnie taki kod wygenerował historyczną tabelę.
