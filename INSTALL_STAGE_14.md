# Instalacja i uruchomienie Etapu 14

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path .\BOHN-Original-Stage-14.zip -DestinationPath . -Force
Remove-Item .\BOHN-Original-Stage-14.zip
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_14.ps1
.\RUN_STAGE_14_SMOKE.ps1
```

Po udanym smoke uruchom:

```powershell
.\RUN_STAGE_14_FULL.ps1
```

Pełny bieg wykonuje trzy historyczne programy i może trwać kilkanaście lub
kilkadziesiąt minut na CPU. Komunikaty `nadal działa` są informacją o postępie.
