# ASD-001R FULL — analiza eksperymentu uzupełniającego

## Werdykt

Pełny, prerejestrowany bieg zakończył się statusem
`STRUCTURAL_RECONSTRUCTION_CONFIRMED`. Wszystkie 40 dopasowań spełniło
zamrożone kryteria. Wynik potwierdza zasadniczą tezę, że rzadki model potrafi
autonomicznie wskazać dwie symetrie rzeczywiście kodujące etykietę wśród 99
kandydatów.

Nie jest to historyczne `EXACT_MATCH`. Eksperyment używa jawnie poprawionego
generatora etykiet i nie dowodzi, która wersja kodu wytworzyła tabelę 4.2.

## Wyniki względem tabeli 4.2

| C | Accuracy ASD-001R | Tabela 4.2 | Delta | Top1 True | Obie Top10 | Obie Top2 | Śr. najlepsza | Śr. najgorsza |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.9169 | 0.9244 | 0.0075 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 |
| 0.05 | 0.9331 | 0.9554 | 0.0223 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 |
| 0.10 | 0.9337 | 0.9630 | 0.0293 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 |
| 0.20 | 0.9230 | 0.9630 | 0.0400 | 10/10 | 10/10 | 10/10 | 1.0 | 2.0 |

Struktura rang tabeli została odtworzona dokładnie. Dokładności są niższe o
`0.0075`--`0.0400`, dlatego porównanie liczb ma status
`DIFFERENCE_AFTER_CORRECTION`.

## Kontrole odporności wniosku

- 40/40 dopasowań ukończono i zaliczono;
- `flip_horizontal` i `rotate_180` miały rangi dokładnie 1 i 2 w 40/40 prób;
- oba bloki miały dodatnią ważność w 40/40 prób;
- słabszy prawdziwy blok zawsze wyprzedzał najlepszego losowego kandydata;
- najmniejszy margines nad kandydatem losowym wyniósł `0.3109`, największy
  `1.4083`;
- połączony sygnał przewyższał najlepszy sygnał pojedynczy w 40/40 kontroli;
- średni zysk ablacyjny wyniósł `0.2146` (zakres `0.1981`--`0.2352`);
- nie wystąpiło żadne ostrzeżenie solvera;
- każdy bieg zawierał dokładnie 99 kandydatów.

## Relacja do historycznego ASD-001

Historyczne źródło pozostaje bez zmian i ma status
`PRIMARY_MATCH_SECONDARY_CODE_TABLE_MISMATCH`: odkrywa obrót, który faktycznie
tworzy jego etykietę, ale nie odtwarza raportowanej rangi odbicia poziomego.

ASD-001R jest osobnym eksperymentem uzupełniającym. Generator jawnie używa obu
symetrii, a protokół został zamrożony po pilocie i przed pełnym biegiem.
Pozytywny wynik pokazuje, że niespójność historycznego kodu z tabelą ma
minimalne, technicznie działające wyjaśnienie zgodne z narracją publikacji.

## Dozwolone sformułowanie

> Teza o autonomicznym odkrywaniu dwóch symetrii rzeczywiście kodujących
> etykietę została potwierdzona w prerejestrowanym, równoległym eksperymencie
> uzupełniającym ASD-001R (40/40 prób; rangi 1–2 wśród 99 kandydatów).

Należy jednocześnie dopisać, że opublikowany listing koduje tylko jedną z tych
symetrii, a dokładności eksperymentu uzupełniającego różnią się od tabeli.
