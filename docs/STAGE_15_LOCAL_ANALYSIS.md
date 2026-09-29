# Etap 15 — analiza lokalnego wykonania

## Wynik ogólny

Pełny bieg `20260928T185044Z` wykonał wszystkie siedem końcowych jednostek
historycznego suite'u kodem 0. Źródło listingu 71 pozostało niezmienione.

- `RF-001`, `RF-002`, `MF-001`, `MF-002`: `CLOSE_NUMERIC_MATCH`,
- `MF-003`, `MF-004`: `CONCLUSION_MATCH`,
- `MF-005`: `NUMERIC_DIFFERENCE` dla jednego ścisłego kryterium 40/40.

Po closeoucie zakończono **115 ze 115** jednostek źródłowego PDF-a; żadna
pozycja nie pozostaje `NOT_RUN`.

## RMIG-FBOHN

`RF-001` i `RF-002` odtworzyły wartości publikacji z największą różnicą
odpowiednio **0,0444 pp** i **0,0500 pp**. Zachowano oba kluczowe porządki:
FBOHN > SRL-12 > BOHN > RAW dla zadania reprezentowalnego oraz
FBOHN > BOHN > RAW dla każdego badanego poziomu szumu poza reprezentacją.

## Meta-FBOHN v1–v4

W `MF-001` i `MF-002` odtworzono dokładnie wynik negatywny: dodatnie wagi
globalne i orbitowe są kasowane przez `StandardScaler`, więc różnica względem
FBOHN wyniosła **0,0 pp**. Learned Orbit Mixing (`MF-003`) poprawił wynik
średnio o **0,1778 pp**, a Symbolic Orbit Composer (`MF-004`) o **2,7736 pp**.

## MF-005 — zakres rozbieżności

| Miara | Publikacja | Lokalnie | Różnica |
|---|---:|---:|---:|
| AUNC FBOHN | 0,6182 | 0,618208 | +0,000008 |
| AUNC poly-control | 0,6249 | 0,624944 | +0,000044 |
| AUNC v4 single | 0,6449 | 0,645944 | +0,001044 |
| AUNC v5 library | 0,6528 | 0,654111 | +0,001311 |
| v5 − FBOHN | +3,46 pp | +3,5903 pp | +0,1303 pp |
| v5 − v4 | +0,79 pp | +0,8167 pp | +0,0267 pp |

Biblioteka v5 wygrała z ręcznym poly-control w **40/40** komórek. Z FBOHN
wygrała w **39/40**. Jedyny wyjątek wystąpił dla szumu `0.5`, seeda `4`:
v5 = **62,9444%**, FBOHN = **63,0000%**, czyli różnica wyniosła zaledwie
**−0,0556 pp**. To właśnie ten pojedynczy wynik powoduje techniczny status
`NUMERIC_DIFFERENCE`; nie jest nim różnica średnich, które są bardzo bliskie.

Operator `mul` pozostał zdecydowanie najczęstszy: **824** wystąpienia wobec
raportowanych 847. `absdiff` uzyskał 266 wobec 263. Najczęstsze symbole
`(M_4*L_0)`, `(M_0*M_4)`, `(L_1*L_2)` i `(M_1*M_2)` zachowują interpretację
publikacji: istotne są iloczynowe sprzężenia średnich orbitowych i składowych
laplasjanowych.

## Ocena merytoryczna

Ścisłe zdanie „v5 wygrywa z FBOHN na 10/10 seedów dla każdego poziomu szumu”
nie zostało dokładnie odtworzone, dlatego repozytorium nie oznacza `MF-005`
jako pełnego `CONCLUSION_MATCH`. Jednocześnie średnia przewaga v5 nad FBOHN,
przewaga nad v4, 40/40 zwycięstw nad poly-control oraz stabilna dominacja
operatora mnożenia zostały potwierdzone. Główny mechanizm Meta-FBOHN v5 jest
zatem zachowany, a rozbieżność dotyczy jednego bardzo ostrego kryterium.

Ocena całego Etapu 15: **NEAR_COMPLETE_REPRODUCTION** — sześć z siedmiu
jednostek zachowuje wszystkie testowane wnioski, a siódma zachowuje mechanizm
i wartości średnie, lecz nie dokładną liczbę 40/40 zwycięstw.
