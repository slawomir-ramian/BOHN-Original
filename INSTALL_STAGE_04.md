# Instalacja Etapu 04

Etap obejmuje cały rozdział SBOHN: `S-001`--`S-011`. Jednostki są zapisane i
uruchamiane w oryginalnej kolejności PDF-a:

```text
S-001, S-002, S-003, S-004, S-005, S-006,
S-010, S-011, S-007, S-008, S-009
```

## Instalacja

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path .\BOHN-Original-Stage-04.zip -DestinationPath . -Force
Remove-Item .\BOHN-Original-Stage-04.zip
.\SETUP_STAGE_04.ps1
```

## Test szybki

```powershell
.\RUN_STAGE_04_SMOKE.ps1
```

Smoke wykonuje testy integralności oraz `S-003` i kontrakt `S-010`. Nie tworzy
ZIP-a wynikowego.

## Pełny przebieg

```powershell
.\RUN_STAGE_04_FULL.ps1
```

Pełny przebieg wykonuje 11 jednostek sekwencyjnie. Najcięższy `S-009` wykonuje
1500 dopasowań regresji logistycznej; przewidywany czas na laptopie to kilka
minut. Po zakończeniu automatycznie powstaje kompletny ZIP w `artifacts\`.

Nie wykonuj commita przed analizą ZIP-a i zamknięciem etapu.
