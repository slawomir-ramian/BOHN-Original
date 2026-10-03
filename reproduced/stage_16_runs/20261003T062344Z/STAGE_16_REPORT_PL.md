# Etap 16 — raport SOTA-002R/SOTA-002H

Tryb: **FULL**  
Wynik ogólny: **PASS**

## Granice interpretacji

- SOTA-002R używa niezmienionych klas historycznych i nie koduje cudzych wyników jako celu.
- Rozdzielczość `3840` w historycznym modelu oznacza obraz kwadratowy 3840×3840, a nie UHD 3840×2160.
- Baseline to dokładnie trzywarstwowy CNN z listingu; nie jest nazywany ResNetem.
- SOTA-002H potwierdza wyłącznie kontrakt strukturalny: stałe parametry i 16 tokenów.
- Nie zgłaszamy stałego czasu całego pipeline'u ani przewagi jakości klasyfikacji.

## SOTA-002R — bezpośredni benchmark

| Rozmiar | SBOHN ms | CNN ms | CNN/SBOHN | Parametry SBOHN | Tokeny |
|---:|---:|---:|---:|---:|---:|
| 28x28 | 3.429 | 0.603 | 0.18× | 54,298 | 16 |
| 112x112 | 3.411 | 2.224 | 0.65× | 101,338 | 16 |
| 448x448 | 4.889 | 28.306 | 5.79× | 853,978 | 16 |
| 1024x1024 | 10.003 | 160.434 | 16.04× | 4,245,466 | 16 |
| 2048x2048 | 38.107 | 806.152 | 21.16× | 16,828,378 | 16 |
| 3840x3840 | 82.975 | 2959.517 | 35.67× | 59,033,562 | 16 |

## SOTA-002H — stałoparametrowy front-end

| Rozmiar | Czas ms | Parametry | Tokeny | Megapiksele |
|---:|---:|---:|---:|---:|
| 28x28 | 4.085 | 51,434 | 16 | 0.001 |
| 112x112 | 4.877 | 51,434 | 16 | 0.013 |
| 448x448 | 7.510 | 51,434 | 16 | 0.201 |
| 1024x1024 | 125.233 | 51,434 | 16 | 1.049 |
| 2048x2048 | 129.054 | 51,434 | 16 | 4.194 |
| 3840x3840 | 284.852 | 51,434 | 16 | 14.746 |
| 1920x1080 | 48.097 | 51,434 | 16 | 2.074 |
| 2560x1440 | 62.165 | 51,434 | 16 | 3.686 |
| 3840x2160 | 145.596 | 51,434 | 16 | 8.294 |

## Wniosek techniczny

Historyczny wariant zachowuje 16 tokenów, lecz jego gęsty embedder rośnie z rozdzielczością. Nowy wariant H usuwa wzrost liczby parametrów, ale nadal musi odczytać i skompresować wszystkie piksele; zatem jego koszt front-endu nie jest O(1).
