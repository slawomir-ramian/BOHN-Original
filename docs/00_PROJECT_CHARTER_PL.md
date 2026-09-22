# Karta projektu BOHN-Original

## Zakres

BOHN-Original obejmuje całą historyczną linię rozwoju opisaną w monografii:
BOHN, SBOHN, odkrywanie symetrii, SBOHN-PL, SBOHN-AR, warianty wysokowymiarowe,
kompresję, Learnable SBOHN, Fractal/Patch/HighRes SBOHN, Meta-SBOHN, adaptację
zadaniową, continual learning, SOTA/scaling, MoE, RMIG-FBOHN i Meta-FBOHN.

Obejmuje także:

- programy konstrukcyjne i testy techniczne;
- benchmarki i kontrole negatywne;
- warianty nieudane i obalające hipotezy;
- pełne oraz częściowe kody z tekstu i dodatków;
- wyniki surowe i tabele, jeśli występują w PDF;
- parametry, seedy i zależności, jeśli zostały podane;
- jawne oznaczenie każdej informacji brakującej.

## Granica względem BOHN Laboratory

Repozytorium jest niezależne od `BOHN-Laboratory-MultiEngine`. Nie wolno
przenosić do rekonstrukcji mechanizmów, poprawek ani wniosków powstałych później,
chyba że zostaną umieszczone w oddzielnej, jednoznacznie oznaczonej warstwie
technicznej.

## Kolejność pracy

1. Inwentaryzacja wszystkich jednostek z PDF.
2. Audyt kompletności i zatwierdzenie indeksu.
3. Ekstrakcja kodu historycznego bez modernizacji.
4. Utworzenie opakowań uruchomieniowych.
5. Odtworzenie środowisk i danych.
6. Reprodukcja lokalna.
7. Porównanie `reported` z `reproduced`.
8. Tagi Git dokumentujące historyczne etapy rozwoju.

