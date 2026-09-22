# Audyt źródłowego LaTeX-a

- SHA-256: `8cb0b6c02e1a3ef6a118bd3a6649ebc8cbf2574f000e317206fa44a9d36cd225`
- Rozdziały i dodatki: **17**.
- Numerowane środowiska tabel: **94**.
- Bloki `lstlisting`: **74**.
- Bloki `verbatim`: **20**.
- Referencje do zewnętrznych grafik: **2**.
- Brakujące grafiki: **2**.

## Wnioski dla indeksu

1. Źródło potwierdza dokładnie 94 numerowane tabele obecne w polskim PDF.
2. Ujawniło dwa osobne elementy SBOHN-LR: kod referencyjny (`S-010`) oraz
   benchmark 100 seedów (`S-011`).
3. Potwierdza, że pełny kod Meta-SBOHN v1, v2, v2+SRL i Meta-Meta-SBOHN v1
   nie występuje w dodatku A.6; pozycje te pozostają `NARRATIVE_ONLY`.
4. Każdy blok źródłowy ma osobny hash SHA-256 i powiązanie z ID eksperymentu.
5. Dwa pełne skrypty Fractal/Patch znajdują się w blokach `verbatim` w tekście
   głównym, a nie w dodatku. Nie wolno ich pominąć podczas ekstrakcji kodu.
6. Źródło nie jest samodzielnie kompilowalne bez dwóch plików PNG:
   `fractal_inpdep_results.png` i `fractal_real_images_results.png`.

## Status

Audyt strukturalny źródła zakończony. Następny etap to ekstrakcja pierwszego
pakietu wykonawczego B-001--B-009 bez modernizacji historycznego kodu.
