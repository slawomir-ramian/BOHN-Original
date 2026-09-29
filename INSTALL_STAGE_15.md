# Instalacja i wykonanie Etapu 15

Etap 15 obejmuje ostatnie siedem jednostek monografii: `RF-001`, `RF-002`
oraz `MF-001`–`MF-005`. Zachowuje pozycje 109–115 dokładnie w kolejności PDF-a.

```powershell
cd E:\BOHN\BOHN-Original
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_15.ps1
.\RUN_STAGE_15_SMOKE.ps1
```

Po wyniku `SMOKE STAGE 15: PASS` uruchom pełny protokół:

```powershell
.\RUN_STAGE_15_FULL.ps1
```

Pełny przebieg jest znacznie cięższy od poprzednich etapów. Szczególnie
`MF-005` wykonuje odkrywanie biblioteki symbolicznej dla 40 komórek, po 12
niezależnych uruchomień ewolucyjnych. Postęp jest zapisywany w
`reproduced/stage_15_checkpoint/`; ponowne uruchomienie wznawia gotowe komórki.
Nie usuwaj tego katalogu przed zakończeniem etapu.

Źródło historyczne z listingu 71 jest przechowywane bez zmian. Checkpointy są
warstwą wykonawczą i nie modyfikują opublikowanego kodu.
