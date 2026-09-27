$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_11.ps1"
}

& .\.venv\Scripts\python.exe tools\audit_latex_source.py
if ($LASTEXITCODE -ne 0) { throw "Audyt źródła LaTeX nie powiódł się." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodła się." }

& .\.venv\Scripts\python.exe tools\render_inventory.py
if ($LASTEXITCODE -ne 0) { throw "Aktualizacja indeksu nie powiodła się." }

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_11.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy closeoutu Etapu 11 nie powiodły się." }

& .\.venv\Scripts\python.exe tools\validate_stage_11_closeout.py
if ($LASTEXITCODE -ne 0) { throw "Walidacja closeoutu Etapu 11 nie powiodła się." }

Write-Host "STAGE 11 CLOSEOUT: PASS" -ForegroundColor Green
