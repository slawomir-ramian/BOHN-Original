# Etap 05 - analiza lokalnej reprodukcji

## Werdykt

Pełny przebieg Etapu 05 potwierdza wartość merytoryczną adaptacyjnego routera
oraz matematyczne własności uogólnienia SBOHN na grupę SO(2). Wszystkie testy i
wszystkie jednostki wykonawcze zakończyły się powodzeniem. Dwie różnice
liczbowe w surowych bazach odniesienia nie podważają głównego wyniku i nie mogą
być traktowane jako ścisła niezgodność programu historycznego, ponieważ dla
tych eksperymentów monografia nie publikuje pełnego generatora danych ani
protokołu.

## Integralność przebiegu

- przebieg: `reproduced/stage_05_runs/20260923T052427Z/`,
- czas rozpoczęcia UTC: `2026-09-23T05:24:27+00:00`,
- środowisko: Windows 10, Python 3.14.5, NumPy 2.5.3,
  scikit-learn 1.9.1, 4 procesory logiczne,
- testy automatyczne: **7/7 PASS**,
- jednostki eksperymentalne: **8/8 PASS**,
- wszystkie pliki `stderr`: puste,
- manifest SHA-256: zweryfikowany bez błędów,
- SHA-256 archiwum wyników:
  `9f83d3ac41e5620935bb427fb878f99d513536219e510610a993a16540b67fd2`.

## Wyniki w chronologii PDF-a

| Poz. | ID | Status końcowy | Ocena merytoryczna | Najważniejszy wynik |
|---:|---|---|---|---|
| 21 | `G-001` | `EXACT_MATCH` | potwierdzony | pełny historyczny wydruk identyczny; Fisher `0.9963 +/- 0.0105` |
| 22 | `SO-001` | `CLOSE_MATCH` | potwierdzony | symetryzator zeruje się do precyzji maszynowej; maks. różnica `4.82e-16` |
| 23 | `SO-002` | `FORMULA_MATCH` | potwierdzony | profil numeryczny zgadza się ze wzorem analitycznym; maks. różnica `8.88e-16` |
| 24 | `SO-003` | `FORMULA_MATCH` | potwierdzony | momenty `M_1`--`M_6` identyczne do raportowanej precyzji |
| 25 | `SO-004` | `FORMULA_MATCH` | potwierdzony | moduły współczynników Fouriera zachowują inwariantność; maks. różnica `5.55e-17` względem wydruku |
| 26 | `SO-005` | `PARTIAL_RECONSTRUCTION` | główny wniosek potwierdzony | SO(2)-SBOHN i oracle `1.000`; surowa LogReg `0.519` wobec `0.535` |
| 27 | `SO-006` | `PARTIAL_RECONSTRUCTION` | główny wniosek potwierdzony | SO(2)-SBOHN `1.000`; surowa baza `0.507` wobec `0.415` |
| 28 | `SO-007` | `CLOSE_MATCH` | potwierdzony | błąd inwariantności `3.42e-13` wobec `1.14e-13`; oba na poziomie dokładności całkowania |

## Granica źródła i rekonstrukcji

`G-001` jest jedyną jednostką tego etapu wykonaną bezpośrednio z pełnego
historycznego programu. Dla `SO-001` zachowano historyczne obliczenie, ale
odtworzono brakujące raportowanie. `SO-002`--`SO-004` zostały odtworzone z
opublikowanych wzorów i wyników, dlatego ich status opisuje zgodność wzorów, a
nie identyczność nieopublikowanego kodu. `SO-005`--`SO-007` korzystają ze
wspólnego opublikowanego fragmentu ekstraktora; generator danych i część
protokołu wykonawczego musiały zostać jawnie zrekonstruowane.

## Interpretacja różnic w SO-005 i SO-006

| Jednostka | Miara | Monografia | Reprodukcja | Różnica |
|---|---|---:|---:|---:|
| `SO-005` | surowe współrzędne, LogReg | 0.535 | 0.519 | -0.016 |
| `SO-005` | surowe współrzędne, RandomForest | 1.000 | 1.000 | 0.000 |
| `SO-005` | SO(2)-SBOHN, LogReg | 1.000 | 1.000 | 0.000 |
| `SO-005` | SO(2)-SBOHN, RandomForest | 1.000 | 1.000 | 0.000 |
| `SO-005` | oracle | 1.000 | 1.000 | 0.000 |
| `SO-006` | surowe współrzędne | 0.415 | 0.507 | +0.092 |
| `SO-006` | SO(2)-SBOHN | 1.000 | 1.000 | 0.000 |

Różnice występują wyłącznie w surowych bazach zależnych od brakujących
szczegółów generatora i protokołu. Reprezentacja relacyjna osiąga raportowane
`1.000` we wszystkich porównaniach. Z tego powodu uczciwym statusem jest
`PARTIAL_RECONSTRUCTION`, a nie `DIVERGENT`.

## Wnioski

1. Historyczny adaptacyjny router Fishera jest reprodukowany dokładnie.
2. Zerowanie symetryzatora, profil analityczny, momenty i własności Fouriera
   zostały potwierdzone do precyzji numerycznej.
3. W eksperymentach R4 i R8 reprezentacja SO(2)-SBOHN zachowuje raportowaną
   skuteczność `1.000`; różnią się jedynie protokołowo wrażliwe bazy surowe.
4. Inwariantność reprezentacji została potwierdzona na poziomie dokładności
   całkowania numerycznego.
5. Chronologia źródłowa pozycji 21--28 została zachowana bez sortowania po ID.

Etap 05 jest zamknięty. Po jego zakończeniu wykonano 28 ze 115 jednostek, a 87
pozostaje do odtworzenia.
