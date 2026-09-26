# Instalacja i uruchomienie Etapu 07

Etap obejmuje cały rozdział 5: jednostki `PL-001`--`CMP-002`, czyli pozycje
34--45 w oryginalnej kolejności PDF-a.

W PowerShell, w katalogu `E:\BOHN\BOHN-Original`, wykonaj:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_07.ps1
.\RUN_STAGE_07_SMOKE.ps1
```

Po zaliczeniu smoke uruchom pełny przebieg:

```powershell
.\RUN_STAGE_07_FULL.ps1
```

## Co wykonuje tryb pełny

- `PL-001`, `AR-001`--`AR-004`, `HD-001` i `HD-002`: niezmienione listingi
  historyczne z monografii. `HD-001` i `HD-002` współdzielą jeden przebieg,
  ponieważ w publikacji stanowią dwa wyjścia tego samego programu.
- `PL-002`, `PL-003`, `HD-003`, `CMP-001`, `CMP-002`: audyt dokładnych
  wyników opublikowanych. Monografia nie zawiera dla nich pełnego kodu,
  dlatego Etap 07 nie przedstawia rekonstrukcji jako źródła historycznego.

Programy ewolucyjne `AR-004` oraz wysokowymiarowy program `HD-001/HD-002`
mogą działać długo. Runner co 60 sekund wypisuje neutralny komunikat
`nadal działa` i po każdej jednostce zapisuje `CHECKPOINT.json`. Kolor czerwony
nie jest używany do komunikatów innych niż rzeczywiste błędy PowerShella.

Wyniki trafiają do `reproduced/stage_07_runs/`, a pełny przebieg tworzy ZIP
w `artifacts/`.
