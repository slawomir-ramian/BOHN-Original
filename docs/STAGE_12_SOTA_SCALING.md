# Etap 12 — porównanie SOTA i skalowanie inferencji

## Zakres

Etap obejmuje dokładnie dwa kolejne eksperymenty w chronologii PDF-a:

1. `SOTA-001` — pozycja 88/115, porównanie jakości na Fashion-MNIST;
2. `SOTA-002` — pozycja 89/115, skalowanie inferencji od 28 do 448 pikseli.

Źródłem wykonawczym są pełne listingi 60 i 61 (A.8.1 i A.8.2). Są zapisane
w `historical/` bez zmian i chronione sumami SHA-256.

## Warstwa zgodności

Historyczne programy zapisują wyniki i dane pod ścieżkami `/tmp`. Runner
tworzy poza `historical/` kopię roboczą, w której przekierowuje wyłącznie te
literały do `reproduced/stage_12_*`. Oryginał jest sprawdzany przed i po
wykonaniu. Nie są zmieniane architektury, hiperparametry, pętle ani liczba
powtórzeń.

## Ważne ograniczenia interpretacyjne

- Nagłówek listingu `SOTA-001` mówi o dwóch epokach, lecz rzeczywista pętla
  wykonuje trzy (`range(3)`). Reprodukcja zachowuje kod, czyli trzy epoki.
- Listing nie ustawia ziarna losowego, zatem dokładności są stochastyczne.
- Czasy treningu i inferencji zależą od CPU, wersji PyTorch, liczby wątków
  oraz chwilowego obciążenia systemu.
- `SOTA-002` używa pojedynczego warm-upu i tylko trzech pomiarów `time.time`.
  To protokół historyczny, ale nie precyzyjny mikrobenchmark.

Dlatego raport osobno klasyfikuje: wykonanie kodu, dokładny kontrakt liczby
parametrów, zgodność wniosku naukowego i różnicę surowych liczb.

## Kryteria

`SOTA-001` otrzymuje `CLOSE_NUMERIC_MATCH`, gdy kontrakt parametrów jest
dokładny, ranking MLP > ViT > SBOHN > CNN zostaje zachowany, a największa
różnica dokładności nie przekracza 5 pp. Przy zachowanym rankingu i kontrakcie,
ale większej różnicy, status to `CONCLUSION_MATCH`.

`SOTA-002` otrzymuje `CLOSE_NUMERIC_MATCH`, gdy kontrakt parametrów jest
dokładny, wykładniki SBOHN i ViT są mniejsze od wykładnika CNN, największa
różnica czasu nie przekracza 2 ms, a różnica wykładnika 0,15. Zachowany wniosek
przy większych różnicach sprzętowych daje `CONCLUSION_MATCH`.
