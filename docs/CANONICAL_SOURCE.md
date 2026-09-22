# Źródło kanoniczne

- Plik: `docs/source/BOHN_PL.pdf`
- Tytuł: *Burnside Orbit Histogram Network (BOHN) i Symmetry-Breaking BOHN (SBOHN): od orbit grupowych do obserwabli złamania symetrii w uczeniu maszynowym*
- Autor: Sławomir Ramian
- Data dokumentu: czerwiec 2026
- Liczba stron PDF: 308
- SHA-256: `1b4d0a1161d50b575a1796a0d67d2ca5696995562772d8b823a4e6f0cd0332a3`

## Źródło pomocnicze - LaTeX angielski

- Plik: `docs/source/BOHN_EN_SOURCE.tex`
- Pochodzenie: źródłowy LaTeX angielskiej wersji monografii, przekazany przez autora
- SHA-256: `8cb0b6c02e1a3ef6a118bd3a6649ebc8cbf2574f000e317206fa44a9d36cd225`
- Rozmiar strukturalny: 17 rozdziałów/dodatków, 94 środowiska `table`,
  74 środowiska `lstlisting`

Polski PDF pozostaje źródłem kanonicznym dla polskiego tekstu, numerów stron i
raportowanych wyników. Angielski LaTeX jest źródłem pomocniczym dla dokładnego
odczytu kodu, podpisów, etykiet i struktury dokumentu. Rozbieżności między nimi
muszą być jawnie raportowane, a nie automatycznie rozstrzygane.

## Numeracja stron

Od części numerowanej monografii numer fizycznej strony PDF jest większy o 1 od
numeru wydrukowanego na stronie. Przykłady:

| Strona drukowana | Strona PDF |
|---:|---:|
| 14 | 15 |
| 145 | 146 |
| 298 | 299 |

W indeksie zapisujemy przede wszystkim numer wydrukowany, bo do niego odwołuje
się spis treści, oraz osobno zakres stron PDF.

## Zasada pierwszeństwa

Jeśli opis narracyjny, listing kodu i tabela wyników są ze sobą niespójne, nie
wybieramy samodzielnie jednej wersji. Rejestrujemy konflikt, zachowujemy wszystkie
warianty źródłowe i odkładamy rozstrzygnięcie do raportu reprodukcji.
