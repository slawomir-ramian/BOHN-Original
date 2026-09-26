# Instalacja Etapu 07R

Pakiet wymaga wcześniej zainstalowanego i zakończonego Etapu 07.

W katalogu `E:\BOHN\BOHN-Original` uruchom:

```powershell
.\SETUP_STAGE_07R.ps1
.\RUN_STAGE_07R_PILOT.ps1
```

Po analizie pilota uruchomimy osobno:

```powershell
.\RUN_STAGE_07R_FULL.ps1
```

Pięć jednostek `R` pozostaje poza chronologią 115 eksperymentów. Pilot i pełny
przebieg automatycznie tworzą osobne ZIP-y wynikowe w `artifacts/`.
