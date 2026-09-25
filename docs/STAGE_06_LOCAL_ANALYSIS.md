# Etap 06 - analiza lokalnej reprodukcji

## Werdykt

Etap 06 został wykonany w pełnej kolejności PDF-a. Jednostki `SD-001`--`SD-004`
uzyskały `CLOSE_NUMERIC_MATCH`. `ASD-001` ukończył wszystkie 40 dopasowań i
otrzymał kwalifikowany status
`PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH`.

Nie jest to awaria wykonania ani odrzucenie mechanizmu wykrywania symetrii.
Najważniejszy wynik kodu został odtworzony: transformacja `rotate_180`, z której
historyczna funkcja `make_labels` faktycznie tworzy etykiety, zajęła pierwsze
miejsce w 40/40 prób.

## ASD-001

| C | Accuracy | Top1 True | Obie w Top10 | Średnia najlepsza ranga | Średnia najgorsza ranga |
|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.9426 | 10/10 | 0/10 | 1.0 | 77.6 |
| 0.05 | 0.9472 | 10/10 | 0/10 | 1.0 | 69.4 |
| 0.10 | 0.9443 | 10/10 | 0/10 | 1.0 | 55.7 |
| 0.20 | 0.9307 | 10/10 | 1/10 | 1.0 | 39.8 |

Tabela 4.2 monografii podaje dla wszystkich wartości `C`: `Top1 True = 10/10`,
`Both True Top10 = 10/10`, średnią najlepszą rangę 1.0 i najgorszą rangę 2.0.
Lokalnie odtworzono pierwszą część, lecz nie drugą.

## Przyczyna rozbieżności

Kod historyczny definiuje zbiór „prawdziwych” kandydatów jako
`flip_horizontal` i `rotate_180`, ale funkcja `make_labels` generuje etykiety
wyłącznie z asymetrii `rotate_180`. Odbicie poziome nie uczestniczy w mechanizmie
tworzenia etykiety. Dlatego jego niska ranga jest zgodna z opublikowanym kodem,
choć nie z pełnym opisem tabeli.

W `scikit-learn 1.9.1` pojawia się również ostrzeżenie o przestarzałym
parametrze `penalty="l1"`; współczesne API zapisuje czystą karę L1 jako
`l1_ratio=1`. Nie zmienia to faktu, że brak odbicia w `make_labels` jest
niezależną i bezpośrednią niespójnością kod--tabela.

## Interpretacja

- potwierdzono zdolność metody do znalezienia symetrii faktycznie kodującej
  etykietę wśród 99 kandydatów;
- nie potwierdzono twierdzenia, że druga transformacja zajmuje miejsce 2 i
  zawsze znajduje się w Top10;
- wynik `ASD-001` należy zachować jako częściową zgodność, bez poprawiania
  historycznego listingu i bez przedstawiania tabeli 4.2 jako w pełni
  reprodukowanej.

## Uzupełniające potwierdzenie ASD-001R

Po tej diagnozie wykonano osobny, prerejestrowany eksperyment ASD-001R z
generatorem jawnie zależnym od obu deklarowanych symetrii. W pełnym biegu z 99
kandydatami uzyskano rangi 1 i 2 w 40/40 prób, dodatni margines nad kandydatami
losowymi oraz dodatnią kontrolę ablacyjną w 40/40 prób.

Wynik `STRUCTURAL_RECONSTRUCTION_CONFIRMED` potwierdza tezę mechanizmu w
równoległym eksperymencie, ale nie zmienia kwalifikacji historycznego kodu.
Dokładności różnią się od tabeli o `0.0075`--`0.0400`. Pełna analiza:
`docs/STAGE_06_ASD_001R_FULL_ANALYSIS.md`.
