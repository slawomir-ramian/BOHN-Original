# Etap 07 — analiza pełnego przebiegu

## Werdykt

Pełny przebieg wszystkich 12 jednostek rozdziału 5 zakończył się statusem
`FULL STAGE 07: PASS`. Siedem jednostek z opublikowanym kodem wykonano bez
modyfikacji, a pięć jednostek bez pełnego kodu zachowano jako
`AUDITED_REPORTED_RESULT`.

| ID | Tryb | Status | Najważniejszy wynik |
|---|---|---|---|
| PL-001 | historyczny | `CLOSE_NUMERIC_MATCH` | evolved `0.9444` wobec raportowanego `0.9481` |
| PL-002 | audyt wyniku | `AUDITED_REPORTED_RESULT` | pełny kod nieopublikowany |
| PL-003 | audyt wyniku | `AUDITED_REPORTED_RESULT` | pełny kod nieopublikowany |
| AR-001 | historyczny | `CLOSE_NUMERIC_MATCH` | evolved `0.9574` wobec `0.9537` |
| AR-002 | historyczny | `CONCLUSION_MATCH` | AR-v2 `0.9611`, random-99 `0.9093` |
| AR-003 | historyczny | `CLOSE_NUMERIC_MATCH` | evolved `0.9574` wobec `0.9537` |
| AR-004 | historyczny | `CLOSE_NUMERIC_MATCH` | perm-sim `0.0312`, CKA `0.7942` |
| HD-001 | historyczny | `CONCLUSION_MATCH` | SBOHN wygrywa `10/10` dla każdego wymiaru |
| HD-002 | współdzielony kod historyczny | `CONCLUSION_MATCH` | gain rośnie `0.1105 → 0.1191 → 0.1322` |
| HD-003 | audyt wyniku | `AUDITED_REPORTED_RESULT` | pełny kod nieopublikowany |
| CMP-001 | audyt wyniku | `AUDITED_REPORTED_RESULT` | pełny kod nieopublikowany |
| CMP-002 | audyt wyniku | `AUDITED_REPORTED_RESULT` | pełny kod nieopublikowany |

## Najważniejsze zgodności

- PL-001 i AR-001/003 odtwarzają raportowane dokładności z odchyleniem
  `0.0037`.
- AR-002 zachowuje główny wniosek: biblioteka wygenerowana ewolucyjnie wraz
  z selekcją przewyższa baseline i 99 losowych permutacji.
- AR-004 bardzo dokładnie odtwarza reprezentacyjne klasy równoważności:
  raportowane `perm-sim=0.0319`, `CKA=0.7965`; lokalnie odpowiednio
  `0.0312` i `0.7942`.
- HD-001 potwierdza dodatnią przewagę SBOHN aż do `d=4095`, po `10/10` wygranych
  w każdym wymiarze.

## Ważna różnica HD-002

Kod historyczny potwierdza wzrost przewagi wraz z liczbą próbek, ale nie
odtwarza liczb tabeli 5.2. Dla `n=2000,5000,10000` lokalne gain wynoszą
`0.1105, 0.1191, 0.1322`, podczas gdy tabela raportuje
`0.063, 0.122, 0.173`. Również lokalny baseline rośnie wyraźnie ponad `0.5`.
Dlatego poprawnym statusem jest `CONCLUSION_MATCH`, a nie zgodność numeryczna.

## Granica dowodowa

Wyników `PL-002`, `PL-003`, `HD-003`, `CMP-001` i `CMP-002` nie wolno nazywać
lokalną reprodukcją kodu historycznego. W Etapie 07 potwierdzono wyłącznie ich
obecność, integralność i treść w monografii. Osobne rekonstrukcje mają sufiks
`R` i są opisane w `STAGE_07R_FULL_ANALYSIS.md`.
