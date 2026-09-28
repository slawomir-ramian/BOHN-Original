# Etap 13 — Hotfix 01

Hotfix rozszerza ścisłą kontrolę integralności listingu 63 o drugi audytowany
wariant źródła. Warianty różnią się wyłącznie językiem trzech linii docstringa
(polski/angielski). Kod wykonywalny pozostaje identyczny.

Kontrola nie została wyłączona: akceptowane są tylko dwa jawnie zapisane hashe
SHA-256. Każdy inny wariant nadal zatrzyma konfigurację Etapu 13.

Po rozpakowaniu ZIP-a do katalogu repozytorium uruchom:

```powershell
cd E:\BOHN\BOHN-Original
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_13.ps1
.\RUN_STAGE_13_SMOKE.ps1
```
