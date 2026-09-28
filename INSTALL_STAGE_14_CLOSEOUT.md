# Instalacja closeoutu Etapu 14

Closeout zapisuje pełny bieg `20260928T180446Z`, aktualizuje 9 pozycji w
inwentarzu i klasyfikuje etap jako częściową reprodukcję: 1 z 3 wykonanych
wniosków zachowany, 2 z 3 niepotwierdzone liczbowo.

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path .\BOHN-Original-Stage-14-Closeout.zip -DestinationPath . -Force
Remove-Item .\BOHN-Original-Stage-14-Closeout.zip
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_STAGE_14_CLOSEOUT.ps1
git status
```

Nie wykonuj commitu przed komunikatem `STAGE 14 CLOSEOUT: PASS`.
