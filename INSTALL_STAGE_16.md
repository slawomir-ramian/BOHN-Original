# Instalacja i uruchomienie Etapu 16

Etap 16 jest **uzupełnieniem** repozytorium BOHN-Original. Nie zmienia kodu
historycznego `SOTA-002`, nie zmienia wydania `v1.0.0` i nie dodaje pozycji do
kanonicznej chronologii 115 eksperymentów.

## 1. Rozpakowanie paczki

Umieść pobrany ZIP w `E:\BOHN\BOHN-Original`, a następnie uruchom w PowerShell:

```powershell
cd E:\BOHN\BOHN-Original

$zip = Get-ChildItem `
  -Path . `
  -Filter "BOHN-Original-Stage-16*.zip" `
  -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $zip) {
    throw "Nie znaleziono ZIP-a Etapu 16 w katalogu repozytorium."
}

Expand-Archive -Path $zip.FullName -DestinationPath . -Force
Remove-Item $zip.FullName
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

## 2. Przygotowanie i test krótki

```powershell
.\SETUP_STAGE_16.ps1
.\RUN_STAGE_16_SMOKE.ps1
```

## 3. Pełny eksperyment

```powershell
.\RUN_STAGE_16_FULL.ps1
```

Pełny przebieg obejmuje obrazy kwadratowe do `3840×3840` oraz, dla nowego
wariantu H, formaty prostokątne do UHD `3840×2160`. Wymaga więcej pamięci niż
test krótki. Wyniki znajdą się w `reproduced\stage_16_runs`, a archiwum wyników
w `artifacts`.

Nie wykonuj jeszcze `git add` ani `git commit`. Najpierw wspólnie ocenimy
raport i czasy.

