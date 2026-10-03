# Etap 16 — lokalna analiza SOTA-002R i SOTA-002H

## Status

**TECHNICAL_CONFIRMATION_WITH_LIMITATIONS**

Etap 16 jest eksperymentem uzupełniającym, wykonanym poza kanoniczną
chronologią 115 jednostek z monografii. Historyczny kod `SOTA-002` nie został
zmieniony; jego SHA-256 został zweryfikowany przed wykonaniem.

Pełny przebieg:

- identyfikator: `20261003T062344Z`;
- system: Windows 10, Python 3.14.5, PyTorch 2.14.0+cpu;
- CPU, 4 wątki, batch 1, `float32`;
- 3 rozgrzewki i 7 pomiarów, mediana `time.perf_counter_ns`;
- manifest: wszystkie 8 wpisów poprawne.

## SOTA-002R — bezpośrednia replikacja

| Rozmiar | Historyczny SBOHN | CNN | CNN/SBOHN | Parametry SBOHN |
|---:|---:|---:|---:|---:|
| 28×28 | 3,429 ms | 0,603 ms | 0,18× | 54 298 |
| 112×112 | 3,411 ms | 2,224 ms | 0,65× | 101 338 |
| 448×448 | 4,889 ms | 28,306 ms | 5,79× | 853 978 |
| 1024×1024 | 10,003 ms | 160,434 ms | 16,04× | 4 245 466 |
| 2048×2048 | 38,107 ms | 806,152 ms | 21,16× | 16 828 378 |
| 3840×3840 | 82,975 ms | 2959,517 ms | 35,67× | 59 033 562 |

W całej siatce liczba tokenów wynosiła 16. Przewaga nad prostym CNN pojawiła
się od 448×448 i rosła wraz z rozdzielczością. Zewnętrznie zgłoszona wartość
61,8× nie była celem testu i nie została dokładnie odtworzona; kierunek oraz
duża przewaga przy wysokiej rozdzielczości zostały potwierdzone.

Profil dla kwadratowego wejścia 3840×3840:

- ekstrakcja łat: 11,391 ms;
- pierwsza warstwa gęsta: 53,395 ms;
- kompletny embedder: 50,641 ms;
- rdzeń relacyjny i głowica: 4,683 ms.

Pomiary składowych są niezależnymi medianami, dlatego nie należy ich dodawać
jak składników pojedynczego pomiaru. Pokazują jednak jednoznacznie, że rdzeń
relacyjny nie jest głównym źródłem kosztu. Historyczny embedder rośnie wraz z
rozdzielczością, osiągając 59 033 562 parametrów przy 3840×3840.

## SOTA-002H — stałoparametrowy wariant hierarchiczny

| Rozmiar | Czas | Parametry | Tokeny |
|---:|---:|---:|---:|
| 28×28 | 4,085 ms | 51 434 | 16 |
| 112×112 | 4,877 ms | 51 434 | 16 |
| 448×448 | 7,510 ms | 51 434 | 16 |
| 1024×1024 | 125,233 ms | 51 434 | 16 |
| 2048×2048 | 129,054 ms | 51 434 | 16 |
| 3840×3840 | 284,852 ms | 51 434 | 16 |
| 1920×1080 | 48,097 ms | 51 434 | 16 |
| 2560×1440 | 62,165 ms | 51 434 | 16 |
| 3840×2160 | 145,596 ms | 51 434 | 16 |

Wariant H używał jednego modelu dla wszystkich rozdzielczości. W porównaniu z
historycznym modelem dla 3840×3840 zmniejszył liczbę parametrów o około 99,91%,
ale nie poprawił czasu inferencji względem historycznej konstrukcji.

Dla prawdziwego UHD 3840×2160:

- cały model: 145,596 ms;
- front-end: 134,480 ms;
- rdzeń relacyjny i głowica: 3,637 ms.

Rdzeń pozostał mały, lecz koszt przetwarzania pikseli nie zniknął.

## Wniosek

Potwierdzono trzy ograniczone, precyzyjne tezy:

1. rdzeń BOHN/Sinkhorn może działać na stałych 16 tokenach;
2. historyczna konstrukcja skaluje się czasowo korzystniej niż użyty prosty CNN
   przy dużych obrazach;
3. nowy front-end usuwa zależność liczby parametrów od rozdzielczości.

Nie potwierdzono i nie zgłasza się następujących mocniejszych tez:

- stałego czasu całego pipeline'u względem liczby pikseli;
- dokładnie 61-krotnego przyspieszenia niezależnego od sprzętu;
- przewagi jakości klasyfikacji wariantu H;
- przewagi czasowej wariantu H nad historycznym SBOHN.

Wynik nie podważa relacyjnej idei BOHN. Rozdziela efektywnie skalujący się
rdzeń od kosztu akwizycji i kompresji wejścia oraz wskazuje front-end jako
miejsce dalszej optymalizacji.

