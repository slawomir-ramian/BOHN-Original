# Etap 07R FULL — analiza rekonstrukcji uzupełniających

## Werdykt

Zamrożony protokół `STAGE_07R_V1` zakończył się statusem
`PARTIAL_SUPPLEMENTARY_CONFIRMATION`. Cztery z pięciu prerejestrowanych
kryteriów zostały potwierdzone. `HD-003R` zachował główny trend średnich, ale
nie spełnił ostrzejszego kryterium wygranej w każdym seedzie.

Eksperymenty pozostają poza chronologią 115 jednostek i nie są odzyskanym
kodem historycznym.

## PL-002R — potwierdzone

- baseline: `0.7537`;
- najlepsza para początkowa: `0.8741`;
- najlepsza para po ewolucji: `0.9463`;
- gain nad baseline: `+0.1926`;
- gain nad startem: `+0.0722`;
- tabela publikacji: `0.9259`, delta rekonstrukcji: `+0.0204`.

Ewolucja pary permutacji działa zgodnie z tezą i zbliża się do kontroli true-pair
`0.9722`.

## PL-003R — kryterium potwierdzone, ścisła monotoniczność nie

| K | Rekonstrukcja | Publikacja | Delta |
|---:|---:|---:|---:|
| 1 | 0.7444 | 0.7778 | -0.0334 |
| 2 | 0.7667 | 0.8130 | -0.0463 |
| 5 | 0.8426 | 0.8333 | +0.0093 |
| 10 | 0.8519 | 0.8481 | +0.0038 |
| 20 | 0.8981 | 0.8537 | +0.0444 |
| 50 | 0.8944 | 0.9093 | -0.0149 |
| 99 | 0.8907 | 0.9167 | -0.0260 |

Nachylenie względem `log(K)` jest dodatnie (`0.03476`), a `K=99` przewyższa
`K=1` i baseline. Prerejestrowane kryterium jest spełnione. Nie odtworzono
jednak ścisłej monotoniczności tabeli: maksimum pojawiło się przy `K=20`, po
czym wystąpił niewielki spadek.

## HD-003R — częściowe potwierdzenie

| d | Baseline | SBOHN | Gain | Wygrane |
|---:|---:|---:|---:|---:|
| 63 | 0.7245 | 0.8440 | +0.1195 | 10/10 |
| 255 | 0.6527 | 0.7208 | +0.0682 | 10/10 |
| 1023 | 0.5425 | 0.5608 | +0.0183 | 7/10 |
| 4095 | 0.5103 | 0.5138 | +0.0035 | 6/10 |

Średni gain jest dodatni dla każdego wymiaru i maleje monotonicznie, co
odtwarza kierunek tabeli. Nie odtworzono jednak postulowanej odporności
per-seed dla dwóch największych wymiarów. Ponadto wystąpiło 10 ostrzeżeń
`ConvergenceWarning`. Ponieważ protokół był zamrożony, nie zwiększano
`max_iter` po zobaczeniu wyniku. Status pozostaje
`STRUCTURAL_RECONSTRUCTION_NOT_CONFIRMED`.

## CMP-001R — potwierdzone

- PCA-48: `0.9630` wobec raportowanego `0.9426`;
- autoenkoder rekonstrukcyjny: `0.8111` wobec `0.7759`;
- przewaga PCA: `0.1519` wobec raportowanego `0.1667`.

Kierunek i wielkość efektu są zbieżne: kompresja PCA zachowuje informację
predykcyjną lepiej niż autoenkoder optymalizujący rekonstrukcję.

## CMP-002R — potwierdzone

- SRL przewyższa PCA dla każdego `k` w `10/10` seedach;
- średnie SRL dla `k=2,4,8,16`: `0.9485, 0.9409, 0.9402, 0.9474`;
- pełna reprezentacja: `0.9719`;
- SRL-2 zachowuje `97.60%` dokładności pełnej reprezentacji;
- publikacja raportuje około `96.97%`.

Teza o niskowymiarowym predykcyjnym latencie została mocno potwierdzona.

## Dozwolone sformułowanie

> W zamrożonych rekonstrukcjach uzupełniających potwierdzono cztery z pięciu
> głównych kryteriów strukturalnych rozdziału 5. Piąta rekonstrukcja,
> proportional-signal, odtworzyła dodatnią i malejącą z wymiarem średnią
> przewagę SBOHN, lecz nie potwierdziła wygranej w każdym seedzie przy dwóch
> największych wymiarach.

Nie wolno na tej podstawie twierdzić, że odzyskano brakujący kod publikacji ani
że wszystkie wartości tabel zostały dokładnie zreprodukowane.
