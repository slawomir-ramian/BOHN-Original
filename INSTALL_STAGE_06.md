# Instalacja i uruchomienie Etapu 06

Etap obejmuje jednostki `SD-001`--`SD-004` oraz `ASD-001`, czyli pozycje
29--33 w oryginalnej kolejności PDF-a.

W PowerShell, w katalogu `E:\BOHN\BOHN-Original`, wykonaj:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_06.ps1
.\RUN_STAGE_06_SMOKE.ps1
```

Po zaliczeniu smoke można uruchomić pełny przebieg:

```powershell
.\RUN_STAGE_06_FULL.ps1
```

Pełny przebieg wykonuje niezmienione listingi historyczne. Jednostka
`ASD-001` może działać bardzo długo. Co 60 sekund runner wypisuje neutralny
komunikat `nadal działa`, a po każdej ukończonej jednostce zapisuje
`CHECKPOINT.json`. Nie przerywaj procesu tylko dlatego, że przez dłuższy czas
nie pojawia się wynik końcowy.

Wyniki trafiają do `reproduced/stage_06_runs/`, a po pełnym przebiegu również
do ZIP-a w `artifacts/`.

Jeśli wyłącznie `ASD-001` osiągnie limit 14 400 sekund, nie uruchamiaj ponownie
całego etapu. Użyj `RUN_STAGE_06_ASD_RECOVERY.ps1`; szczegóły znajdują się w
`INSTALL_STAGE_06_RECOVERY.md`.
