# Etap 13 — system zintegrowany i bateria CPU

## Zakres

Etap obejmuje pozycje 90–99 w kolejności PDF-a:

- `SYS-001`–`SYS-005` — cztery kierunki badawcze i system zintegrowany;
- `CPU-001`–`CPU-005` — pięć eksperymentów pełnej baterii CPU.

## Granica publikowanego kodu

Listing 62 definiuje `PatchEncoder`, `DeepPatchEncoder`, `PermGenerator` i
`MoERouter`, ale kończy się przed ładowaniem danych, treningiem i ewaluacją.
Nie może sam wygenerować tabel `SYS-001`–`SYS-004`.

Listing 63 definiuje kompletną architekturę `BOHNIntegratedSystem`, lecz nie
zawiera scenariusza treningowego ani obliczenia tabel `SYS-005`. Z tego powodu
pięć pozycji `SYS` otrzymuje uczciwy status `AUDITED_REPORTED_RESULT`.

Listing 64 zawiera cały wspólny protokół `CPU-001`–`CPU-005`: pobranie czterech
zbiorów, przygotowanie próbek, architektury, trening oraz wydruki wyników.

## Błąd techniczny listingu 64

Kod wywołuje `gc.collect()`, ale nie zawiera `import gc`. Plik historyczny jest
zachowany bajtowo. Warstwa wykonawcza tworzy kopię roboczą, w której:

1. przekierowuje `/tmp/data` do lokalnego cache repozytorium;
2. dodaje brakujący `import gc`.

Obie zmiany są zapisane w provenance i nigdy nie nadpisują oryginału.

## Klasyfikacja

Wspólny program jest wykonywany tylko raz. Wynik tekstowy zostaje sparsowany
oddzielnie dla pięciu ID. `CLOSE_NUMERIC_MATCH` wymaga zachowania wniosku i
maksymalnej różnicy do 5 pp. Przy zachowanym wniosku i większej różnicy status
to `CONCLUSION_MATCH`; brak wniosku daje `NUMERIC_DIFFERENCE`.

Program jest obliczeniowo znacznie cięższy od smoke: trenuje wiele modeli oraz
może przy pierwszym uruchomieniu pobrać MNIST, FashionMNIST, KMNIST i CIFAR-10.
