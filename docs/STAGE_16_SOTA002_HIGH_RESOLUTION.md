# Etap 16: kontrolowany eksperyment wysokich rozdzielczości SOTA-002

## Cel

Etap odpowiada na trafną obserwację z niezależnego uruchomienia `SOTA-002`:
rdzeń relacyjny może pracować na stałych 16 tokenach, ale historyczny front-end
nadal wykonuje pracę zależną od liczby pikseli, a jego pierwsza warstwa liniowa
rośnie wraz z rozdzielczością.

## Dwie oddzielne jednostki

### SOTA-002R

Bezpośrednia replikacja wydajności klas `FractalSBOHN` i `CNN` z zachowanego
listingu. Kod historyczny jest kontrolowany hashem SHA-256 i nie jest
modyfikowany. Rozszerzamy jedynie siatkę rozdzielczości i stosujemy medianę
pomiarów `time.perf_counter_ns`.

Wartość `3840` oznacza tutaj obraz kwadratowy `3840×3840`. Nie należy jej
utożsamiać ze standardowym formatem UHD `3840×2160`. Baseline jest prostym
trzywarstwowym CNN dokładnie takim jak w listingu.

### SOTA-002H

Jawnie nowy wariant architektury. Dwa sploty i adaptacyjne uśrednianie tworzą
siatkę `4×4`, czyli zawsze 16 tokenów o szerokości 16. Następnie używany jest
ten sam kontrakt rdzenia Sinkhorn `16 → 8 → 4 → 2`.

Ten wariant ma jeden, stały zestaw parametrów dla wszystkich badanych
rozdzielczości. Nie oznacza to stałego czasu całego pipeline'u: front-end nadal
musi odczytać i skompresować wejściowe piksele.

## Zamrożony protokół

- CPU, 4 wątki, batch 1, `float32`;
- `model.eval()` i `torch.inference_mode()`;
- zegar `time.perf_counter_ns`, raportowana mediana;
- pełna siatka kwadratowa: 28, 112, 448, 1024, 2048, 3840;
- dodatkowa siatka H×W dla wariantu H: 1080×1920, 1440×2560, 2160×3840;
- oddzielny pomiar front-endu i rdzenia relacyjnego.

## Granice wnioskowania

Etap 16 nie jest eksperymentem treningowym i nie dowodzi przewagi jakości
klasyfikacji nowego wariantu H. Potwierdza wyłącznie własności strukturalne i
mierzy wydajność inferencji. Wynik zewnętrznego autora jest motywacją i punktem
porównawczym, ale nie jest zakodowany jako warunek zaliczenia.

