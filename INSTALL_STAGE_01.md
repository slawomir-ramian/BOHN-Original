# Instalacja Etapu 01 w istniejącym repozytorium

Repozytorium `E:\BOHN\BOHN-Original` powinno być puste poza katalogiem `.git`.

1. Pobierz `BOHN_ORIGINAL_STAGE_01_INDEX_v1.zip` do katalogu repozytorium.
2. W PowerShellu uruchom:

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive .\BOHN_ORIGINAL_STAGE_01_INDEX_v1.zip -DestinationPath . -Force
Remove-Item .\BOHN_ORIGINAL_STAGE_01_INDEX_v1.zip
python .\tools\render_inventory.py
git status
```

Oczekiwany komunikat walidatora:

```text
OK: 103 unique inventory rows
```

Nie wykonuj jeszcze `git add` ani `git commit`. Najpierw wspólnie sprawdzimy
wynik `git status` i zawartość indeksu.

