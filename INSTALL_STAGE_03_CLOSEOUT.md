# Zamknięcie Etapu 03

Pakiet aktualizuje statusy `B-001`--`B-009`, regeneruje czytelny indeks i dodaje
raport z lokalnej reprodukcji. Nie zmienia listingów historycznych ani zapisanych
wyników lokalnych.

Po rozpakowaniu do katalogu głównego repozytorium uruchom:

```powershell
.\APPLY_STAGE_03_CLOSEOUT.ps1
git status
```

Commit wykonujemy dopiero po usunięciu redundantnego wyniku smoke i sprawdzeniu
pełnej listy zmian.
