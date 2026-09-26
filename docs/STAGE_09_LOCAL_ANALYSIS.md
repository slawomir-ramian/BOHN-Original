# Etap 09 — analiza pełnej reprodukcji lokalnej

## Zakres i środowisko

Pełny bieg z `2026-09-26T19:45:22Z` objął pozycje 57--72 źródłowej
chronologii PDF-a: `FR-001`, `FR-004`, `FR-002`, `FR-003`, `PT-001`,
`PT-002`, `PT-003`, `PT-004`, `PT-005` oraz `HR-001`--`HR-007`.

Wykonanie przeprowadzono w Windows 10, Pythonie 3.14.5, NumPy 2.5.3,
scikit-learn 1.9.1 i PyTorch 2.14.0+cpu. Manifest SHA-256 pełnego przebiegu
jest zgodny, a wszystkie pliki `stderr` są puste.

## Klasyfikacja jednostek

| Jednostki | Liczba | Klasyfikacja | Znaczenie |
|---|---:|---|---|
| `FR-002`, `FR-003`, `PT-001`, `PT-002`, `PT-004`, `PT-005` | 6 | `CLOSE_NUMERIC_MATCH` | uruchomiono niezmieniony kod historyczny; wniosek naukowy zachowany |
| `FR-001`, `FR-004`, `PT-003`, `HR-001`--`HR-007` | 10 | `AUDITED_REPORTED_RESULT` | zachowano wynik publikacji, ale PDF nie zawiera kompletnego kodu docelowego |

Status audytowy nie oznacza wyniku negatywnego. Oznacza wyłącznie, że nie ma
podstaw do przedstawienia lokalnego uruchomienia jako reprodukcji kodu, który
nie został opublikowany.

## Wyniki Fractal SBOHN

Program z rozdziału 7.2 odtworzył wszystkie liczby z publikacji dokładnie do
raportowanej precyzji.

| Zbiór | Konfiguracja | Publikacja | Reprodukcja | Różnica |
|---|---|---:|---:|---:|
| MNIST | Frac-2L | 0.7675 | 0.7675 | 0 |
| MNIST | Frac-3L | 0.8825 | 0.8825 | 0 |
| MNIST | Frac-4L | 0.8950 | 0.8950 | 0 |
| MNIST | Frac-4L h=64 | 0.9000 | 0.9000 | 0 |
| MNIST | MLP-128 | 0.9075 | 0.9075 | 0 |
| Fashion-MNIST | Frac-2L | 0.6700 | 0.6700 | 0 |
| Fashion-MNIST | Frac-3L | 0.7675 | 0.7675 | 0 |
| Fashion-MNIST | Frac-4L | 0.8025 | 0.8025 | 0 |
| Fashion-MNIST | MLP-96 | 0.7975 | 0.7975 | 0 |
| Fashion-MNIST | MLP-128 | 0.8125 | 0.8125 | 0 |

Wniosek o korzyści głębokości jest potwierdzony. Na Fashion-MNIST Frac-4L
osiąga 0.8025, czyli o 0.0050 więcej niż MLP-96, zgodnie z publikacją.

## Wyniki Patch SBOHN

Wyniki programu z rozdziału 7.3 różnią się od wartości tabelarycznych jedynie
śladem precyzji `float32`. Największa bezwzględna różnica wynosi
`2.6702880906448456e-08`.

| Porównanie | MNIST | Fashion-MNIST | Wniosek |
|---|---:|---:|---|
| MLP | 0.9160 | 0.8420 | punkt odniesienia |
| InpDep 4H, tau=0.1 | 0.9180 | 0.8480 | przewaga odpowiednio 0.002 i 0.006 |
| Global, tau=0.3 | 0.8640 | 0.7400 | punkt ablation |
| InpDep 1H, tau=0.3 | 0.9160 | 0.8320 | zysk 0.052 i 0.092 względem Global |
| InpDep 1H, tau=0.1 | 0.9080 | 0.8220 | punkt ablation |
| InpDep 4H, tau=0.1 | 0.9180 | 0.8480 | zysk 0.010 i 0.026 względem 1H |

Potwierdzono trzy główne tezy programu: niewielką przewagę najlepszej
konfiguracji nad MLP, wyraźną korzyść input-dependency oraz korzyść czterech
głów względem jednej.

## Granica źródłowa

- `FR-001` i `FR-004` mają wyniki i fragmenty opisu, lecz nie kompletny kod
  docelowego eksperymentu.
- `PT-003` dzieli kontekst z opublikowanym programem Patch SBOHN, ale ten
  program nie wykonuje sweepu rozdzielczości opisanego w tabeli.
- `HR-001`--`HR-007` są raportowane narracyjnie i tabelarycznie bez kompletnego
  programu historycznego.

W tych dziesięciu przypadkach repozytorium zachowuje dokładny materiał
źródłowy i jego hash, bez tworzenia fikcyjnego kodu historycznego.

## Wniosek końcowy

Etap 09 ma mocne potwierdzenie numeryczne: wszystkie sześć jednostek, dla
których monografia udostępnia kompletny kod, zachowuje wnioski i odtwarza
wartości z maksymalną różnicą około `2.67e-08`. Po zamknięciu etapu ukończone
są 72 ze 115 kanonicznych jednostek PDF-a; pozostają 43.
