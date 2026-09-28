# Instalacja closeoutu Etapu 13

Closeout zapisuje pełny bieg `20260928T051822Z`, koryguje granice źródłowe
pozycji `SYS`/`CPU` i klasyfikuje wynik jako częściową reprodukcję: 3 z 5
wniosków CPU zachowane, 2 z 5 niepotwierdzone.

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path .\BOHN-Original-Stage-13-Closeout.zip -DestinationPath . -Force
Remove-Item .\BOHN-Original-Stage-13-Closeout.zip
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_STAGE_13_CLOSEOUT.ps1
git status
```

Nie wykonuj commitu przed komunikatem `STAGE 13 CLOSEOUT: PASS`.
