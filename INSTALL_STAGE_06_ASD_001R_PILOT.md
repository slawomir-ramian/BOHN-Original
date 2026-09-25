# Instalacja i uruchomienie pilota ASD-001R

Po rozpakowaniu nakładki do katalogu repozytorium uruchom:

```powershell
.\RUN_STAGE_06_ASD_001R_PILOT.ps1
```

Skrypt korzysta z istniejącego środowiska Etapu 06. Jeżeli `.venv` nie istnieje,
najpierw uruchom `.\SETUP_STAGE_06.ps1`.

Pilot zapisuje checkpoint po każdym dopasowaniu. Po zakończeniu tworzy raport w
`reproduced/stage_06_asd_001r_pilot/` i paczkę wynikową w `artifacts/`.

`PILOT_NON_CONFIRMATORY` oznacza, że wyniku nie wolno przedstawiać jako
potwierdzenia tabeli 4.2. Techniczne zakończenie skryptu i rezultat merytoryczny
są raportowane osobno.
