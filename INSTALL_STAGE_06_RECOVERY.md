# Odzyskanie ASD-001 po limicie czasu

Historyczny przebieg z 23 września 2026 r. ukończył około 35 z 40 dopasowań,
lecz został zatrzymany przez techniczny limit 14 400 sekund. Nie był to błąd
merytoryczny modelu.

Skrypt `RUN_STAGE_06_ASD_RECOVERY.ps1` wykonuje tę samą konstrukcję danych,
te same 97 losowych kandydatów, podziały, wartości `C`, solver `saga`, karę L1
i limit 5000 iteracji. Oryginalny listing pozostaje nietknięty. Różnica dotyczy
wyłącznie bezpiecznej organizacji wykonania:

- każde z 40 dopasowań jest osobnym zadaniem,
- dwa zadania mogą działać równolegle,
- po każdym zadaniu zapisywany jest checkpoint,
- po przerwaniu ponowne uruchomienie kontynuuje od ostatniego checkpointu,
- komunikat postępu co 60 sekund jest neutralny kolorystycznie.

Uruchomienie:

```powershell
.\RUN_STAGE_06_ASD_RECOVERY.ps1
```

Checkpoint znajduje się w `reproduced/stage_06_asd_checkpoint/`. Nie usuwaj go
przed zakończeniem. Po sukcesie powstanie końcowy katalog
`reproduced/stage_06_runs/*_RECOVERED` oraz ZIP w `artifacts/`.
