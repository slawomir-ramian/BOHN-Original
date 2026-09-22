# Raport audytu indeksu - Etap 01

- Łączna liczba jednostek: **103**.
- Liczba unikalnych identyfikatorów: **103**.
- Jawnie oznaczone jednostki negatywne/obalające: **11**.
- Wszystkie pozycje mają wskazany rozdział, sekcję, strony, źródło kodu,
  informację o wynikach raportowanych i status reprodukcji.
- Zweryfikowano regułę numeracji: strona PDF = strona drukowana + 1
  w numerowanej części dokumentu.

## Liczba jednostek według rozdziału

| Rozdział | Liczba |
|---:|---:|
| 2 | 9 |
| 3 | 9 |
| 4 | 13 |
| 5 | 12 |
| 6 | 11 |
| 7 | 8 |
| 8 | 10 |
| 9 | 4 |
| 10 | 2 |
| 11 | 10 |
| 12 | 8 |
| 13 | 2 |
| 14 | 5 |

## Pokrycie kodem źródłowym w PDF

| Poziom | Liczba |
|---|---:|
| `FULL` | 53 |
| `FULL_IN_CHAPTER` | 4 |
| `FULL_SUITE` | 17 |
| `FULL_UNCAPTIONED` | 12 |
| `NARRATIVE_ONLY` | 8 |
| `PARTIAL` | 8 |
| `PARTIAL_IN_CHAPTER` | 1 |

## Zastrzeżenie

Rejestr rozdziela osobne baterie, podtesty i warianty, nawet gdy korzystają z
jednego wspólnego skryptu. To celowe: żaden wynik lub wariant nie może zniknąć
pod zbiorczą nazwą programu. Przed rekonstrukcją kodu wykonamy drugi audyt
krzyżowy: indeks vs wszystkie tabele, listingi A.1-A.43 i B.1 oraz surowe bloki
wyników bez podpisu `Listing`.
