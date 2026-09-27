# Zamknięcie Etapu 12

Po rozpakowaniu paczki closeout do katalogu repozytorium uruchom:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_STAGE_12_CLOSEOUT.ps1
git status
```

Skrypt ponownie sprawdza audyt LaTeX, chronologię 115 jednostek, indeks,
8 testów Etapu 12, manifest pełnego biegu oraz dokładne wartości zapisane w
`20260927T184235Z`.

Do Git trafia pełny wynik Etapu 12 wskazany przez `LATEST_RUN.txt`. Cache
Fashion-MNIST, tymczasowa kopia zgodności i checkpointy pozostają ignorowane.
