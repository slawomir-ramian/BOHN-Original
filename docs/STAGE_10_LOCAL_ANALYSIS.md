# Etap 10 — analiza pełnej reprodukcji lokalnej

## Zakres i integralność

Pełny bieg z `2026-09-26T21:13:42Z` objął pozycje 73--82 źródłowej
chronologii PDF-a: `MS-001`--`MS-010`. Manifest SHA-256 wszystkich 386 plików
jest zgodny. Program ukończył 180/180 komórek: 20 seedów, trzy zadania i trzy
tryby. Wszystkie 180 strumieni `stderr` komórek oraz wszystkie główne pliki
`stderr` są puste.

Środowisko wykonania: Windows 10, Python 3.14.5, NumPy 2.5.3,
scikit-learn 1.9.1 i pandas 3.0.6, cztery procesory logiczne użyte przez runner.

## Klasyfikacja jednostek

| Jednostki | Liczba | Klasyfikacja | Znaczenie |
|---|---:|---|---|
| `MS-009`, `MS-010` | 2 | `CLOSE_NUMERIC_MATCH` | wykonano pełny wspólny program historyczny |
| `MS-005`--`MS-008` | 4 | `AUDITED_REPORTED_RESULT` | opublikowano tylko fragment inicjalizacji populacji |
| `MS-001`--`MS-004` | 4 | `AUDITED_REPORTED_RESULT` | opublikowano opis i tabele bez kodu docelowego |

Status audytowy nie jest wynikiem negatywnym. Oznacza, że repozytorium nie
przedstawia brakującego programu jako historycznej reprodukcji.

## MS-009 — stała regularyzacja geometrii

| Zadanie | Tryb | Publikacja | Reprodukcja | Różnica |
|---|---|---:|---:|---:|
| Easy | accuracy only | 0.9104 | 0.91130 | +0.00090 |
| Easy | fixed geometry | 0.9057 | 0.90889 | +0.00319 |
| Medium | accuracy only | 0.8894 | 0.89074 | +0.00134 |
| Medium | fixed geometry | 0.8897 | 0.88991 | +0.00021 |
| Hard | accuracy only | 0.8882 | 0.88759 | -0.00061 |
| Hard | fixed geometry | 0.8940 | 0.89417 | +0.00017 |

Największa różnica wynosi `0.0031889`. Na zadaniu trudnym stała regularyzacja
zwiększa średnią accuracy z `0.88759` do `0.89417`, potwierdzając główny
wniosek publikacji. Na zadaniu średnim różnica jest bardzo mała i lokalnie ma
znak `-0.00083`, podczas gdy tabela podaje `+0.0004`; nie zmienia to oceny
materialnej ani deklarowanej niestabilności małych efektów.

## MS-010 — geometry annealing

### Accuracy

| Zadanie | Accuracy only | Fixed geometry | Annealed geometry | Publikacja annealed |
|---|---:|---:|---:|---:|
| Easy | 0.91130 | 0.90889 | **0.92194** | 0.9226 |
| Medium | 0.89074 | 0.88991 | **0.89102** | 0.8902 |
| Hard | 0.88759 | **0.89417** | 0.89259 | 0.8929 |

Układ wyników jest taki sam jak w publikacji: annealing jest najlepszy dla
easy i medium, a stała geometria pozostaje najlepsza dla hard.

### Podobieństwo do prawdziwej transformacji

| Zadanie | Accuracy only | Fixed geometry | Annealed geometry | Publikacja annealed |
|---|---:|---:|---:|---:|
| Easy | 0.10938 | 0.09141 | **0.13203** | 0.1250 |
| Medium | 0.07188 | 0.07266 | **0.11797** | 0.1164 |
| Hard | 0.05781 | 0.07266 | **0.09375** | 0.0930 |

Annealing zwiększa średnie podobieństwo względem `accuracy_only` na wszystkich
trzech zadaniach. Największa bezwzględna różnica względem tabeli wynosi
`0.01014375` i dotyczy `fixed_geometry` dla medium, a nie głównego wyniku
annealingu.

## Basiny geometryczne

Najmocniejsza kontrola mechanizmu odtworzyła się dokładnie:

- medium: `P(acc >= 0.92 i sim >= 0.25)` wzrosło z `0.00` do `0.15`;
- hard: ta sama częstość wzrosła z `0.00` do `0.05`.

Oznacza to trzy z 20 seedów dla medium i jeden z 20 seedów dla hard. Wynik
potwierdza tezę, że annealing nie tylko poprawia średnie podobieństwo, lecz
zwiększa prawdopodobieństwo wejścia do rzadkich, interpretowalnych basinów
geometrycznych.

## Wniosek końcowy

Oba eksperymenty z pełnym kodem uzyskały `CLOSE_NUMERIC_MATCH`, a ich główne
wnioski naukowe zostały zachowane. Różnice mieszczą się na poziomie około
jednego punktu procentowego lub mniej i nie zmieniają relacji pomiędzy
wariantami. Po zamknięciu Etapu 10 ukończone są 82 ze 115 kanonicznych
jednostek PDF-a; pozostają 33.
