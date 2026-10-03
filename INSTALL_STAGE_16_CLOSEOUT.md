# Zamknięcie Etapu 16

Ta paczka zapisuje kontrolowaną analizę wyników `20261003T062344Z`, dodaje
walidator closeout i idempotentnie aktualizuje dokumentację publiczną.

Nie zmienia historycznego kodu `SOTA-002`, nie dodaje pozycji do kanonicznych
115 jednostek i nie wykonuje operacji Git.

## Instalacja

Umieść ZIP w katalogu `E:\BOHN\BOHN-Original`, a następnie uruchom:

```powershell
cd E:\BOHN\BOHN-Original

$zip = Get-ChildItem `
  -Path ".", "$env:USERPROFILE\Downloads" `
  -Filter "BOHN-Original-Stage-16-Closeout.zip" `
  -File `
  -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $zip) {
    throw "Nie znaleziono ZIP-a zamkniecia Etapu 16."
}

Expand-Archive -Path $zip.FullName -DestinationPath . -Force
Remove-Item $zip.FullName
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

.\APPLY_STAGE_16_CLOSEOUT.ps1
git status
```

Po otrzymaniu `STAGE 16 CLOSEOUT: PASS` wklej wynik `git status`. Commit
wykonamy dopiero po sprawdzeniu listy plików.

