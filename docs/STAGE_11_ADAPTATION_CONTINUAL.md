# Etap 11 — adaptacja zadaniowa i continual learning

## Zakres

Etap zachowuje pozycje 83–87 monografii w kolejności PDF-a:

1. `AD-001` — sześć metod adaptacji Perm+Head,
2. `AD-002` — few-shot MNIST → Fashion-MNIST,
3. `AD-003` — head-only vs full-tune,
4. `CL-001` — przełączanie zadań Perm+Head,
5. `CL-002` — przełączanie samych permutacji w większym modelu.

## Wynik audytu kodu

Pierwotny rejestr oznaczał wszystkie pięć jednostek jako `FULL`. Dokładna
kontrola LaTeX-u wykazała, że dwa wspólne listingi kończą się w miejscu
najważniejszych faz:

- listing 58: `PHASE 2` i `PHASE 3` są komentarzami z odsyłaczem do pliku,
  którego nie ma w monografii;
- listing 59: pętle metod few-shot oraz continual learning są wyłącznie
  komentarzowym opisem.

Z tego powodu granicę skorygowano na `SOURCE_FRAGMENT_ONLY`. Oryginalne
fragmenty są przechowywane i haszowane bez modyfikacji.

## Jawna rekonstrukcja

`STAGE_11_RECONSTRUCTION_V1` zachowuje opublikowane architektury, liczby
parametrów, zbiory danych, rozmiary prób, bazowe epoki, optymalizator i seed
podany w listingu 59. Brakujące fazy otrzymują jawne, zamrożone decyzje:

- listing 58: osiem epok adaptacji i `lr=0.003`, zgodnie z fazą bazową;
- listing 59: pięć epok adaptacji i `lr=0.001`, zgodnie z fazą bazową;
- listing 58, który nie podaje seeda: rekonstrukcja używa `seed=42`;
- wyniki dwóch wspólnych programów są używane przez pięć jednostek bez
  powtarzania treningu.

Status `CLOSE_NUMERIC_MATCH` lub `CONCLUSION_MATCH` dotyczy rekonstrukcji, nie
autentyczności brakującego historycznego kodu. Najmocniejszy test continual
learning jest strukturalny: zapisanie i ponowne załadowanie modułu zadaniowego
ma przywrócić wynik dokładnie, ponieważ enkoder pozostaje zamrożony.
