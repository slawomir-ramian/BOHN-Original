# Instalacja i uruchomienie Etapu 10

Etap 10 obejmuje 10 pozycji rozdziału 8 w oryginalnej kolejności PDF-a:
`MS-001`--`MS-010`.

Uruchom w PowerShell z katalogu `E:\BOHN\BOHN-Original`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

.\SETUP_STAGE_10.ps1
.\RUN_STAGE_10_SMOKE.ps1
.\RUN_STAGE_10_FULL.ps1
```

Pełny program historyczny istnieje dla `MS-009` i `MS-010`. Jest wykonywany
raz dla 20 seedów, trzech zadań i trzech trybów, czyli dla 180 niezależnych
komórek. Domyślnie używane są maksymalnie cztery procesy, po jednym wątku BLAS
na proces.

Wyniki każdej ukończonej komórki są zapisywane w:

```text
reproduced\stage_10_checkpoint\cells
```

Jeśli pełny bieg zostanie przerwany, ponowne uruchomienie
`.\RUN_STAGE_10_FULL.ps1` wznowi dokładnie ten sam protokół. Nie usuwaj
checkpointu przed zakończeniem.

`MS-005`--`MS-008` mają jedynie opublikowany fragment inicjalizacji populacji,
a `MS-001`--`MS-004` nie mają kompletnego kodu docelowego. Są zachowane jako
`AUDITED_REPORTED_RESULT`.

Po pełnym przebiegu powstanie archiwum:

```text
artifacts\BOHN_ORIGINAL_STAGE_10_RESULTS_<czas_UTC>.zip
```
