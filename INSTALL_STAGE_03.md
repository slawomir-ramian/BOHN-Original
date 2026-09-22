# Instalacja Etapu 03

Pakiet należy rozpakować bezpośrednio do istniejącego repozytorium
`E:\BOHN\BOHN-Original`. Nie tworzy drugiego repozytorium i nie zawiera `.git`.

## 1. Rozpakowanie

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path "$HOME\Downloads\BOHN-Original-Stage-03.zip" -DestinationPath . -Force
```

## 2. Środowisko

```powershell
.\SETUP_STAGE_03.ps1
```

Skrypt tworzy lokalne `.venv`, instaluje NumPy i scikit-learn oraz ponownie
sprawdza hashe historycznych listingów.

## 3. Szybki test

```powershell
.\RUN_STAGE_03_SMOKE.ps1
```

## 4. Pełna reprodukcja

```powershell
.\RUN_STAGE_03_FULL.ps1
```

Wyniki trafiają do nowego katalogu
`reproduced\stage_03_runs\<czas_UTC>`. Każde uruchomienie zachowuje osobny
`results.json` i raport. Automatycznie powstaje też ZIP w `artifacts\`.

## 5. Kontrola przed commitem

```powershell
git status
git diff --check
```

Nie wykonuj commita, dopóki wynik pełnej reprodukcji nie zostanie wspólnie
przejrzany. Status `DIVERGENT` jest wynikiem audytu, a nie awarią skryptu.
