# Closeout ASD-001R

Nakładka zapisuje pełny wynik ASD-001R, analizę metodologiczną i osobny rejestr
eksperymentów uzupełniających. Nie modyfikuje historycznego źródła ASD-001 ani
kanonicznej chronologii 115 jednostek.

Po rozpakowaniu uruchom:

```powershell
.\APPLY_STAGE_06_ASD_001R_CLOSEOUT.ps1
git status
```

Skrypt sprawdza manifest wyniku, zamrożony hash protokołu, wszystkie 40 zadań,
kontrole rang i ablacji oraz rozdzielenie rejestru PDF-a od eksperymentów
uzupełniających.

Commit wykonaj dopiero po uzyskaniu komunikatu
`STAGE 06 ASD-001R CLOSEOUT: PASS` i sprawdzeniu `git status`.
