# Instalacja i uruchomienie Etapu 08

Uruchom w PowerShell z katalogu `E:\BOHN\BOHN-Original`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

.\SETUP_STAGE_08.ps1
.\RUN_STAGE_08_SMOKE.ps1
.\RUN_STAGE_08_FULL.ps1
```

`SETUP_STAGE_08.ps1` doinstaluje PyTorch do istniejącego środowiska `.venv`. Pakiet może być duży, więc pierwsza instalacja może potrwać kilka minut.

Pełny przebieg wykonuje trzy opublikowane programy w kolejności PDF-a. `LS-002`–`LS-006` zostaną jawnie zapisane jako audyt wyników źródłowych, ponieważ opublikowany listing 53 nie zawiera ich kodu docelowego.

Po pełnym przebiegu powstanie archiwum:

```text
artifacts\BOHN_ORIGINAL_STAGE_08_RESULTS_<czas_UTC>.zip
```
