$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_07.ps1"
}

& .\.venv\Scripts\python.exe tools\audit_latex_source.py
if ($LASTEXITCODE -ne 0) { throw "Audyt źródła LaTeX nie powiódł się." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodła się." }

& .\.venv\Scripts\python.exe tools\render_inventory.py
if ($LASTEXITCODE -ne 0) { throw "Aktualizacja indeksu nie powiodła się." }

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_07*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy closeoutu Etapu 07/07R nie powiodły się." }

& .\.venv\Scripts\python.exe tools\validate_stage_07_closeout.py
if ($LASTEXITCODE -ne 0) { throw "Walidacja closeoutu Etapu 07/07R nie powiodła się." }

Write-Host "STAGE 07/07R CLOSEOUT: PASS" -ForegroundColor Green
