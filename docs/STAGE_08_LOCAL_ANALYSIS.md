# Etap 08 — analiza pełnego przebiegu

## Werdykt

Pełny przebieg pozycji 46–56 zakończył się statusem `FULL STAGE 08: PASS`.
Wszystkie trzy opublikowane programy wykonano bez modyfikacji kodu. Sześć
jednostek, których kod docelowy jest rzeczywiście obecny w listingach,
uzyskało `CLOSE_NUMERIC_MATCH` i zachowało wnioski monografii.

| ID | Tryb | Status | Najważniejszy wynik |
|---|---|---|---|
| LS-001 | historyczny | `CLOSE_NUMERIC_MATCH` | InpDep Task B `0.7241` wobec `0.722` |
| LS-002 | audyt wyniku | `AUDITED_REPORTED_RESULT` | kod EXP 1 nieobecny w listingu 53 |
| LS-003 | audyt wyniku | `AUDITED_REPORTED_RESULT` | kod EXP 2 nieobecny w listingu 53 |
| LS-004 | audyt wyniku | `AUDITED_REPORTED_RESULT` | kod EXP 3 nieobecny w listingu 53 |
| LS-005 | audyt wyniku | `AUDITED_REPORTED_RESULT` | kod EXP 4 nieobecny w listingu 53 |
| LS-006 | audyt wyniku | `AUDITED_REPORTED_RESULT` | kod EXP 5 nieobecny w listingu 53 |
| LD-001 | historyczny | `CLOSE_NUMERIC_MATCH` | DS error przy tau=0.001: `0.34472` vs `0.30013` |
| LD-002 | współdzielony kod historyczny | `CLOSE_NUMERIC_MATCH` | 5/5 wariantów stabilnych; fixed tau `0.89074` |
| LD-003 | współdzielony kod historyczny | `CLOSE_NUMERIC_MATCH` | entropia `1.63733 → 1.22272` bez straty accuracy |
| LD-004 | historyczny | `CLOSE_NUMERIC_MATCH` | no-reg `0.87778`, entropia `0.58642` |
| LD-005 | współdzielony kod historyczny | `CLOSE_NUMERIC_MATCH` | accuracy `0.82778`; 0/3 twardych permutacji |

## LS-001 — pięciokrokowy pipeline

Wyniki niemal dokładnie odtwarzają tabelę:

| Model | Monografia | Lokalnie | Różnica |
|---|---:|---:|---:|
| SBOHN-v1 fixed, Task A | 0.8320 | 0.8315 | -0.0005 |
| SBOHN-v1 annealing, Task A | 0.8740 | 0.8741 | +0.0001 |
| SBOHN-InpDep, Task A | 0.8780 | 0.8778 | -0.0002 |
| MLP, Task B | 0.7190 | 0.7185 | -0.0005 |
| SBOHN-InpDep, Task B | 0.7220 | 0.7241 | +0.0021 |

Zachowano oba główne wnioski: annealing poprawia globalny SBOHN-v1, a model
Input-Dependent przewyższa MLP w ślepym odkrywaniu symetrii.

## Log-Domain Sinkhorn

- `LD-001`: dla tau `0.001` log-domain obniża błąd DS z `0.34472` do
  `0.30013`, zgodnie z tabelą.
- `LD-002`: wszystkie pięć wariantów kończy się bez NaN. Najlepszy pozostaje
  stały tau `0.5` z accuracy `0.89074` wobec raportowanego `0.893`.
- `LD-003`: lambda entropii `0.1` redukuje entropię z `1.63733` do `1.22272`
  przy identycznym accuracy `0.85741`.
- `LD-004`: wariant bez regularyzacji pozostaje najlepszy (`0.87778`), a jego
  naturalna entropia `0.58642` niemal dokładnie odtwarza `0.586`.
- `LD-005`: odtworzono accuracy `0.82778` wobec `0.828`, liczby unikalnych
  kolumn `63/64`, `60/64`, `60/64`, najbliższe symetrie i struktury cykli.

Maksymalne odchylenie wartości kontrolowanej wyniosło `0.0022593`.

## Granica dowodowa LS-002–LS-006

Inwentarz LaTeX przypisywał listing 53 do wszystkich sześciu pozycji LS.
Audyt treści wykazał jednak, że listing wykonuje wyłącznie pięciokrokowy
pipeline `LS-001`. Nie ma w nim pętli ani modeli generujących tabele EXP 1–5.
Dlatego status `FULL` dla `LS-002`–`LS-006` został doprecyzowany do
`SHARED_LISTING_TARGET_CODE_ABSENT`, a wynik do `AUDITED_REPORTED_RESULT`.
Jest to korekta granicy źródłowej, nie negatywny wynik naukowy.

## Ostrzeżenie PyTorch

W `LD-001`–`LD-003` zapisano jedno ostrzeżenie `UserWarning` o konwersji
tensora z `requires_grad=True` do skalaru. Program zakończył się kodem 0,
wszystkie wartości są skończone, a ostrzeżenie nie wpływa na wynik. Nie jest
to błąd wykonania.

## Integralność

- manifest SHA-256: wszystkie pliki `OK`;
- Python `3.14.5`, PyTorch `2.14.0+cpu`, NumPy `2.5.3`, scikit-learn `1.9.1`;
- 4 logiczne procesory;
- chronologia 115 jednostek pozostaje niezmieniona.
