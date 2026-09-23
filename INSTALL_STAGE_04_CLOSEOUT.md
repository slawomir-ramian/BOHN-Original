# Zamknięcie Etapu 04

Pakiet aktualizuje statusy `S-001`--`S-011`, regeneruje czytelny indeks i dodaje
raport z lokalnej reprodukcji. Nie zmienia kodu historycznego, raportowanych
wyników ani zapisanych wyników lokalnych. Chronologia PDF-a pozostaje nadrzędna
wobec numeracji ID.

Po rozpakowaniu do katalogu głównego repozytorium uruchom:

```powershell
.\APPLY_STAGE_04_CLOSEOUT.ps1
git status
```

Commit wykonujemy dopiero po sprawdzeniu pełnej listy zmian i usunięciu
redundantnego przebiegu smoke. Pełny przebieg
`reproduced/stage_04_runs/20260922T221033Z/` pozostaje w repozytorium.
