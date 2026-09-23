# Zamknięcie Etapu 05

Pakiet aktualizuje statusy `G-001` oraz `SO-001`--`SO-007`, regeneruje
czytelny indeks i dodaje raport z lokalnej reprodukcji. Nie zmienia kodu
historycznego, wyników raportowanych ani zapisanych wyników lokalnych.
Chronologia PDF-a pozostaje nadrzędna wobec numeracji ID.

Po rozpakowaniu do katalogu głównego repozytorium uruchom:

```powershell
.\APPLY_STAGE_05_CLOSEOUT.ps1
git status
```

Commit wykonujemy dopiero po sprawdzeniu pełnej listy zmian i pozostawieniu
wyłącznie pełnego przebiegu
`reproduced/stage_05_runs/20260923T052427Z/`.
