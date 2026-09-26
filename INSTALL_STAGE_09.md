# Instalacja i uruchomienie Etapu 09

Etap 09 obejmuje 16 pozycji rozdziału 7 w oryginalnej kolejności PDF-a.

Uruchom w PowerShell z katalogu `E:\BOHN\BOHN-Original`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

.\SETUP_STAGE_09.ps1
.\RUN_STAGE_09_SMOKE.ps1
.\RUN_STAGE_09_FULL.ps1
```

Pełny przebieg uruchamia dwa kompletne, wspólne programy historyczne:

- `FR-002` i `FR-003` — Fractal SBOHN na MNIST/Fashion-MNIST;
- `PT-001`, `PT-002`, `PT-004`, `PT-005` — Patch SBOHN.

Pozostałe 10 pozycji jest zapisywanych jako `AUDITED_REPORTED_RESULT`, ponieważ
monografia zawiera ich tabele lub narrację, lecz nie kompletny kod docelowy.

Pierwszy pełny przebieg pobiera MNIST i Fashion-MNIST. Dane są zachowywane w
`reproduced\stage_09_dataset_cache`, więc drugi przebieg nie pobiera ich ponownie.

Po pełnym przebiegu powstanie archiwum:

```text
artifacts\BOHN_ORIGINAL_STAGE_09_RESULTS_<czas_UTC>.zip
```
