# Instalacja i uruchomienie Etapu 11

Etap 11 obejmuje pozycje 83–87 w oryginalnej kolejności PDF-a:
`AD-001`, `AD-002`, `AD-003`, `CL-001`, `CL-002`.

## Ważna granica źródłowa

Listingi 58 i 59 publikują architektury, przygotowanie danych i fazę bazową,
ale właściwe pętle adaptacji i continual learning zastępują komentarzami.
Repozytorium zachowuje te fragmenty bez zmian, a brakujące fazy wykonuje jako
jawną rekonstrukcję `STAGE_11_RECONSTRUCTION_V1`. Nie jest ona przedstawiana
jako odzyskany kod historyczny.

## Polecenia

```powershell
cd E:\BOHN\BOHN-Original
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_11.ps1
.\RUN_STAGE_11_SMOKE.ps1
.\RUN_STAGE_11_FULL.ps1
```

Pierwszy pełny bieg pobierze MNIST i Fashion-MNIST do lokalnego cache. Dwie
wspólne rekonstrukcje są zapisywane w `reproduced/stage_11_checkpoint/`, więc
przerwany lub powtórzony bieg może wykorzystać ukończoną część.

Pełne wyniki trafiają do `reproduced/stage_11_runs/<UTC>/`, a archiwum do
`artifacts/BOHN_ORIGINAL_STAGE_11_RESULTS_<UTC>.zip`.
