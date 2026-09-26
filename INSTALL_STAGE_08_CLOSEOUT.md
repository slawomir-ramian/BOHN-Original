# Closeout Etapu 08

Po rozpakowaniu paczki closeout do katalogu głównego repozytorium uruchom:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_STAGE_08_CLOSEOUT.ps1
git status
```

Skrypt ponownie sprawdzi źródło LaTeX, chronologię 115 pozycji, inwentarz,
testy Etapu 08, manifest pełnego przebiegu oraz statusy reprodukcji.
