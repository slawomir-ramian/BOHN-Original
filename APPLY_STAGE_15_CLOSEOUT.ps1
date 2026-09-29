$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_15.ps1"
}

& .\.venv\Scripts\python.exe tools\audit_latex_source.py
if ($LASTEXITCODE -ne 0) { throw "Audyt zrodla LaTeX nie powiodl sie." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodla sie." }

& .\.venv\Scripts\python.exe tools\render_inventory.py
if ($LASTEXITCODE -ne 0) { throw "Aktualizacja indeksu nie powiodla sie." }

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_15
if ($LASTEXITCODE -ne 0) { throw "Testy closeoutu Etapu 15 nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\validate_stage_15_closeout.py
if ($LASTEXITCODE -ne 0) { throw "Walidacja closeoutu Etapu 15 nie powiodla sie." }

Write-Host "STAGE 15 CLOSEOUT: PASS" -ForegroundColor Green
