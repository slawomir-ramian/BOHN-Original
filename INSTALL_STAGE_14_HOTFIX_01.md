# Etap 14 — Hotfix 01

Hotfix usuwa zależność ekstraktora od języka podpisów tabel w źródle LaTeX.
Tabele Etapu 14 są identyfikowane po audytowanej pozycji w zbiorze 94 tabel.
Nie zmienia to kodu historycznego, wyników ani chronologii PDF.

Po rozpakowaniu nakładki uruchom ponownie:

```powershell
.\SETUP_STAGE_14.ps1
.\RUN_STAGE_14_SMOKE.ps1
```
