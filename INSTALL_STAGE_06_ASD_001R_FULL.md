# Uruchomienie pełnego ASD-001R

Po rozpakowaniu nakładki do katalogu repozytorium uruchom:

```powershell
.\RUN_STAGE_06_ASD_001R_FULL.ps1
```

Skrypt używa środowiska Etapu 06. Jeżeli `.venv` nie istnieje, najpierw
uruchom `.\SETUP_STAGE_06.ps1`.

Pełny bieg obejmuje 40 dopasowań z 99 blokami cech. Może trwać kilka godzin.
Co 60 sekund pojawia się neutralny komunikat postępu, a po każdym dopasowaniu
zapisywany jest checkpoint. Przerwanie nie usuwa ukończonych zadań; ponowne
uruchomienie kontynuuje pracę.

Po zakończeniu powstają:

- raport w `reproduced/stage_06_asd_001r_full/<czas>/`,
- ZIP wynikowy w `artifacts/BOHN_ORIGINAL_STAGE_06_ASD_001R_FULL_*.zip`.

Nie wykonuj commita przed analizą końcowego ZIP-a i zastosowaniem closeoutu.
