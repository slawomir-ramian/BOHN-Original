# Raport audytu indeksu - Etap 02

- Łączna liczba jednostek: **115**.
- Liczba unikalnych identyfikatorów: **115**.
- Jawnie oznaczone jednostki negatywne/obalające: **11**.
- Zmapowane numerowane tabele wynikowe i porównawcze: **94**.
- Zmapowane niepodpisane lub wieloeksperymentalne bloki kodu: **24**.
- Zmapowane środowiska LaTeX `lstlisting`: **74**.
- Zmapowane środowiska LaTeX `verbatim`: **20**.
- Wszystkie pozycje mają wskazany rozdział, sekcję, strony, źródło kodu,
  informację o wynikach raportowanych i status reprodukcji.
- Zweryfikowano regułę numeracji: strona PDF = strona drukowana + 1
  w numerowanej części dokumentu.

## Liczba jednostek według rozdziału

| Rozdział | Liczba |
|---:|---:|
| 2 | 9 |
| 3 | 11 |
| 4 | 13 |
| 5 | 12 |
| 6 | 11 |
| 7 | 16 |
| 8 | 10 |
| 9 | 5 |
| 10 | 2 |
| 11 | 10 |
| 12 | 9 |
| 13 | 2 |
| 14 | 5 |

## Pokrycie kodem źródłowym w PDF

| Poziom | Liczba |
|---|---:|
| `CHAPTER_NARRATIVE_TARGET_CODE_ABSENT` | 2 |
| `FULL` | 39 |
| `FULL_IN_CHAPTER` | 6 |
| `FULL_SHARED_LISTING` | 8 |
| `FULL_SUITE` | 11 |
| `FULL_UNCAPTIONED` | 14 |
| `NARRATIVE_ONLY` | 16 |
| `PARTIAL` | 4 |
| `SHARED_LISTING_TARGET_CODE_ABSENT` | 6 |
| `SOURCE_FRAGMENT_ONLY` | 9 |

## Wynik audytu krzyżowego

Audyt rozdzielił wcześniej zgrupowane ablacje i warianty z rozdziałów 7, 9 i 12.
Każda z 94 numerowanych tabel jest przypisana do co najmniej jednego ID, a każdy
zidentyfikowany blok kodu w dodatkach ma wskazane jednostki docelowe. Pozycje
`NARRATIVE_ONLY` pozostają jawne i nie będą traktowane jak pełny kod źródłowy.
